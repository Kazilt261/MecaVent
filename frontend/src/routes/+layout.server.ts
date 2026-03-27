import { env } from "$env/dynamic/private";
import { get } from "svelte/store";
import type { LayoutServerLoad } from "./$types";
import { getHost } from "$lib/utils/get_host";

interface userData {
    id: number,
    username: string,
    email: string,
}

export const load: LayoutServerLoad = async ({ depends, cookies, url, request}) => {
    depends("app:auth");
    if (url.pathname.startsWith("/admin")){
        return {}
    }
    const backendUrl = env.URL_BACKEND ?? "http://back-dev:5000";
    const jwt = cookies.get("jwt");
    const reset_jwt = cookies.get("reset_jwt");
    if (!jwt && !reset_jwt) {
        return {}
    }
    if (jwt) {
        const response = await fetch(`${backendUrl}/auth`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${jwt}`,
                "x-tenant-host": getHost(request),
            },
        });
        if (!response.ok) {
            cookies.delete("jwt", { path: "/" });
            cookies.delete("reset_jwt", { path: "/" });
            return {}
        }
        const result = await response.json();
        return {
            user: result as userData
        }
    }
}