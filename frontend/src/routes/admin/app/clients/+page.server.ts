import { env } from "$env/dynamic/private";
import { fail, type Actions } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";

interface Client {
	id: number;
	name_client: string;
	db_client: string;
	redis_client: string;
}

const getAdminHeaders = (jwt: string) => ({
	"Content-Type": "application/json",
	Authorization: `Bearer ${jwt}`,
});

const parseError = async (response: Response): Promise<string> => {
	try {
		const data = await response.json();
		if (typeof data?.detail === "string") {
			return data.detail;
		}
	} catch {
		// keep default
	}
	return "Request failed";
};

const asPositiveInt = (value: string | null, fallback: number): number => {
	if (value === null || value.trim() === "") return fallback;
	const parsed = Number.parseInt(value, 10);
	return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
};

export const load: PageServerLoad = async ({ cookies, url }) => {
	const jwt = cookies.get("jwt_admin");
	const backendUrl = `${env.URL_BACKEND ?? "http://back-dev:5000"}/admin/apps/clients`;

	const search = url.searchParams.get("search") ?? "";
	const sortBy = url.searchParams.get("sort_by") ?? "name_client";
	const sortOrder = url.searchParams.get("sort_order") ?? "asc";
	const limit = asPositiveInt(url.searchParams.get("limit"), 50);
	const offset = asPositiveInt(url.searchParams.get("offset"), 0);

	const query = new URLSearchParams({
		search,
		sort_by: sortBy,
		sort_order: sortOrder,
		limit: String(limit),
		offset: String(offset),
	});

	const meta = {
		search,
		sort_by: sortBy,
		sort_order: sortOrder,
		limit,
		offset,
		total: 0,
	};

	if (!jwt) {
		return { clients: [] as Client[], meta, error: "Unauthorized" };
	}

	const response = await fetch(`${backendUrl}?${query.toString()}`, {
		method: "GET",
		headers: getAdminHeaders(jwt),
	});

	if (!response.ok) {
		return { clients: [] as Client[], meta, error: await parseError(response) };
	}

	const result = await response.json();
	return {
		clients: (result.clients ?? []) as Client[],
		meta: result.meta ?? meta,
	};

};

export const actions = {
	create: async ({ request, cookies }) => {
		const jwt = cookies.get("jwt_admin");
		if (!jwt) {
			return fail(401, { error: true, message: "Unauthorized" });
		}

		const backendUrl = `${env.URL_BACKEND ?? "http://back-dev:5000"}/admin/apps/clients`;
		const data = await request.formData();

		const payload = {
			name_client: String(data.get("name_client") ?? "").trim(),
			db_client: String(data.get("db_client") ?? "").trim(),
			redis_client: String(data.get("redis_client") ?? "default").trim() || "default",
		};

		const response = await fetch(backendUrl, {
			method: "POST",
			headers: getAdminHeaders(jwt),
			body: JSON.stringify(payload),
		});

		if (!response.ok) {
			return fail(response.status, { error: true, message: await parseError(response) });
		}

		return { success: true, action: "create" };
	},

	update: async ({ request, cookies }) => {
		const jwt = cookies.get("jwt_admin");
		if (!jwt) {
			return fail(401, { error: true, message: "Unauthorized" });
		}

		const data = await request.formData();
		const clientId = Number(data.get("client_id"));
		if (!Number.isFinite(clientId) || clientId <= 0) {
			return fail(400, { error: true, message: "Invalid client_id" });
		}

		const payload: Record<string, string> = {};
		const nameClient = String(data.get("name_client") ?? "").trim();
		const dbClient = String(data.get("db_client") ?? "").trim();
		const redisClient = String(data.get("redis_client") ?? "").trim();

		if (nameClient) payload.name_client = nameClient;
		if (dbClient) payload.db_client = dbClient;
		if (redisClient) payload.redis_client = redisClient;

		if (Object.keys(payload).length === 0) {
			return fail(400, { error: true, message: "No fields to update" });
		}

		const backendUrl = `${env.URL_BACKEND ?? "http://back-dev:5000"}/admin/apps/clients/${clientId}`;
		const response = await fetch(backendUrl, {
			method: "PUT",
			headers: getAdminHeaders(jwt),
			body: JSON.stringify(payload),
		});

		if (!response.ok) {
			return fail(response.status, { error: true, message: await parseError(response) });
		}

		return { success: true, action: "update" };
	},

	delete: async ({ request, cookies }) => {
		const jwt = cookies.get("jwt_admin");
		if (!jwt) {
			return fail(401, { error: true, message: "Unauthorized" });
		}

		const data = await request.formData();
		const clientId = Number(data.get("client_id"));
		if (!Number.isFinite(clientId) || clientId <= 0) {
			return fail(400, { error: true, message: "Invalid client_id" });
		}

		const backendUrl = `${env.URL_BACKEND ?? "http://back-dev:5000"}/admin/apps/clients/${clientId}`;
		const response = await fetch(backendUrl, {
			method: "DELETE",
			headers: getAdminHeaders(jwt),
		});

		if (!response.ok) {
			return fail(response.status, { error: true, message: await parseError(response) });
		}

		return { success: true, action: "delete" };
	},
} satisfies Actions;