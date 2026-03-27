import { env } from "$env/dynamic/private";
import { fail } from "@sveltejs/kit";
import type { Actions, PageServerLoad } from "./$types";

interface Client {
	id: number;
	name_client: string;
	db_client: string;
	redis_client: string;
}

interface ClientUrl {
	id: number;
	id_app: number;
	urls: string;
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
	const baseUrl = `${env.URL_BACKEND ?? "http://back-dev:5000"}/admin/apps/clients`;

	const clientsSearch = url.searchParams.get("clients_search") ?? "";
	const clientsSortBy = url.searchParams.get("clients_sort_by") ?? "name_client";
	const clientsSortOrder = url.searchParams.get("clients_sort_order") ?? "asc";
	const clientsLimit = asPositiveInt(url.searchParams.get("clients_limit"), 50);
	const clientsOffset = asPositiveInt(url.searchParams.get("clients_offset"), 0);

	const urlsSearch = url.searchParams.get("urls_search") ?? "";
	const urlsSortBy = url.searchParams.get("urls_sort_by") ?? "id";
	const urlsSortOrder = url.searchParams.get("urls_sort_order") ?? "asc";
	const urlsLimit = asPositiveInt(url.searchParams.get("urls_limit"), 50);
	const urlsOffset = asPositiveInt(url.searchParams.get("urls_offset"), 0);

	const clientsMeta = {
		search: clientsSearch,
		sort_by: clientsSortBy,
		sort_order: clientsSortOrder,
		limit: clientsLimit,
		offset: clientsOffset,
		total: 0,
	};

	const urlsMeta = {
		search: urlsSearch,
		sort_by: urlsSortBy,
		sort_order: urlsSortOrder,
		limit: urlsLimit,
		offset: urlsOffset,
		total: 0,
	};

	const clientsQuery = new URLSearchParams({
		search: clientsSearch,
		sort_by: clientsSortBy,
		sort_order: clientsSortOrder,
		limit: String(clientsLimit),
		offset: String(clientsOffset),
	});

	if (!jwt) {
		return {
			clients: [] as Client[],
			urls: [] as ClientUrl[],
			clientsMeta,
			urlsMeta,
			selectedClientId: null,
			error: "Unauthorized",
		};
	}

	const clientsResponse = await fetch(`${baseUrl}?${clientsQuery.toString()}`, {
		method: "GET",
		headers: getAdminHeaders(jwt),
	});

	if (!clientsResponse.ok) {
		return {
			clients: [] as Client[],
			urls: [] as ClientUrl[],
			clientsMeta,
			urlsMeta,
			selectedClientId: null,
			error: await parseError(clientsResponse),
		};
	}

	const clientsResult = await clientsResponse.json();
	const clients = (clientsResult.clients ?? []) as Client[];
	const loadedClientsMeta = clientsResult.meta ?? clientsMeta;

	const requestedClientId = Number(url.searchParams.get("client_id"));
	const selectedClientId = Number.isFinite(requestedClientId) && requestedClientId > 0
		? requestedClientId
		: (clients[0]?.id ?? null);

	if (!selectedClientId) {
		return {
			clients,
			urls: [] as ClientUrl[],
			clientsMeta: loadedClientsMeta,
			urlsMeta,
			selectedClientId: null,
		};
	}

	const urlsQuery = new URLSearchParams({
		search: urlsSearch,
		sort_by: urlsSortBy,
		sort_order: urlsSortOrder,
		limit: String(urlsLimit),
		offset: String(urlsOffset),
	});

	const urlsResponse = await fetch(`${baseUrl}/${selectedClientId}/urls?${urlsQuery.toString()}`, {
		method: "GET",
		headers: getAdminHeaders(jwt),
	});

	if (!urlsResponse.ok) {
		return {
			clients,
			urls: [] as ClientUrl[],
			clientsMeta: loadedClientsMeta,
			urlsMeta,
			selectedClientId,
			error: await parseError(urlsResponse),
		};
	}

	const urlsResult = await urlsResponse.json();
	return {
		clients,
		urls: (urlsResult.urls ?? []) as ClientUrl[],
		clientsMeta: loadedClientsMeta,
		urlsMeta: urlsResult.meta ?? urlsMeta,
		selectedClientId,
	};
};

export const actions = {
	create: async ({ request, cookies }) => {
		const jwt = cookies.get("jwt_admin");
		if (!jwt) {
			return fail(401, { error: true, message: "Unauthorized" });
		}

		const baseUrl = `${env.URL_BACKEND ?? "http://back-dev:5000"}/admin/apps/clients`;
		const data = await request.formData();

		const clientId = Number(data.get("client_id"));
		const clientUrl = String(data.get("urls") ?? "").trim();
		if (!Number.isFinite(clientId) || clientId <= 0) {
			return fail(400, { error: true, message: "Invalid client_id" });
		}
		if (!clientUrl) {
			return fail(400, { error: true, message: "urls is required" });
		}

		const response = await fetch(`${baseUrl}/${clientId}/urls`, {
			method: "POST",
			headers: getAdminHeaders(jwt),
			body: JSON.stringify({ urls: clientUrl }),
		});

		if (!response.ok) {
			return fail(response.status, { error: true, message: await parseError(response) });
		}

		return { success: true, action: "create", client_id: clientId };
	},

	update: async ({ request, cookies }) => {
		const jwt = cookies.get("jwt_admin");
		if (!jwt) {
			return fail(401, { error: true, message: "Unauthorized" });
		}

		const baseUrl = `${env.URL_BACKEND ?? "http://back-dev:5000"}/admin/apps/clients`;
		const data = await request.formData();

		const clientId = Number(data.get("client_id"));
		const urlId = Number(data.get("url_id"));
		const clientUrl = String(data.get("urls") ?? "").trim();

		if (!Number.isFinite(clientId) || clientId <= 0) {
			return fail(400, { error: true, message: "Invalid client_id" });
		}
		if (!Number.isFinite(urlId) || urlId <= 0) {
			return fail(400, { error: true, message: "Invalid url_id" });
		}
		if (!clientUrl) {
			return fail(400, { error: true, message: "urls is required" });
		}

		const response = await fetch(`${baseUrl}/${clientId}/urls/${urlId}`, {
			method: "PUT",
			headers: getAdminHeaders(jwt),
			body: JSON.stringify({ urls: clientUrl }),
		});

		if (!response.ok) {
			return fail(response.status, { error: true, message: await parseError(response) });
		}

		return { success: true, action: "update", client_id: clientId };
	},

	delete: async ({ request, cookies }) => {
		const jwt = cookies.get("jwt_admin");
		if (!jwt) {
			return fail(401, { error: true, message: "Unauthorized" });
		}

		const baseUrl = `${env.URL_BACKEND ?? "http://back-dev:5000"}/admin/apps/clients`;
		const data = await request.formData();

		const clientId = Number(data.get("client_id"));
		const urlId = Number(data.get("url_id"));

		if (!Number.isFinite(clientId) || clientId <= 0) {
			return fail(400, { error: true, message: "Invalid client_id" });
		}
		if (!Number.isFinite(urlId) || urlId <= 0) {
			return fail(400, { error: true, message: "Invalid url_id" });
		}

		const response = await fetch(`${baseUrl}/${clientId}/urls/${urlId}`, {
			method: "DELETE",
			headers: getAdminHeaders(jwt),
		});

		if (!response.ok) {
			return fail(response.status, { error: true, message: await parseError(response) });
		}

		return { success: true, action: "delete", client_id: clientId };
	},
} satisfies Actions;