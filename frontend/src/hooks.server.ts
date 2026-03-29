import { env } from "$env/dynamic/private";
import { getHost } from "$lib/utils/get_host";
import type { Handle } from "@sveltejs/kit";

interface TenantData {
    tenant_id: number;
    name_client: string;
}

export const handle: Handle = async ({ event, resolve }) => {
    const backendUrl = env.URL_BACKEND

    // check if tenant_id cookie exists
    const tenantIdCookie = event.cookies.get("tenant_id");
    if (tenantIdCookie) {
        // if exists, set tenant_data in locals
        event.locals.tenant_data = {
            tenant_id: parseInt(tenantIdCookie),
            name_client: event.cookies.get("tenant_name") || "",
        } as TenantData;
    }

    else{
        // get data from app_client
        const data_client = await fetch(
            `${backendUrl}/app/tenant_id?host_name=${getHost(event.request)}`,{
                method: "GET",
            }
        )

        const tenant_data: TenantData = await data_client.json();
        event.locals.tenant_data = tenant_data || null;

        if (tenant_data) {
            event.cookies.set("tenant_id", tenant_data?.tenant_id.toString(), {path: "/", httpOnly: true, sameSite: "lax", expires: new Date(Date.now() + 24 * 60 * 60 * 1000)});
            event.cookies.set("tenant_name", tenant_data?.name_client, {path: "/", httpOnly: true, sameSite: "lax", expires: new Date(Date.now() + 24 * 60 * 60 * 1000)});
        }
    }
    

    // get data about user
    const cookies = event.cookies;
    if (event.url.pathname.startsWith("/.well-known")) {
        return resolve(event);
    }

    let jwt = cookies.get("jwt");
    let refreshToken = cookies.get("refresh_jwt");
    let admin_mode = false;

    if (event.url.pathname.startsWith("/admin")) {
        jwt = cookies.get("jwt_admin");
        refreshToken = cookies.get("refresh_jwt_admin");
        admin_mode = true;
    }

    const request = event.request;

    if (!jwt && refreshToken) {
        try {
            
            console.log("host:", getHost(request));
            const response = await fetch(`${backendUrl}${admin_mode ? "/admin" : ""}/auth/refresh`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "x-tenant-host": getHost(request),
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (response.ok) {
                const result = await response.json();

                const newJwt = result?.user_data?.jwt;
                const newRefresh = result?.user_data?.reset_jwt;

                if (newJwt) {
                    cookies.set("jwt", newJwt, {
                        path: "/",
                        httpOnly: true,
                        sameSite: "lax",
                        expires: new Date(Date.now() + 60 * 60 * 1000)
                    });
                }

                if (newRefresh) {
                    cookies.set("refresh_jwt", newRefresh, {
                        path: "/",
                        httpOnly: true,
                        sameSite: "lax",
                        expires: new Date(Date.now() + 24 * 60 * 60 * 1000)
                    });
                }
            } else {
                console.log("refresh falló:", response.status);
                console.error("jwt:", jwt);
                console.error("refreshToken:", refreshToken);
            }

        } catch (err) {
            console.error("error en refresh:", err);

        }
    }

    return resolve(event);
};