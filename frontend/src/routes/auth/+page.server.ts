import { fail, redirect, type Actions } from "@sveltejs/kit";
import { env } from "$env/dynamic/private";
import type { PageServerLoad } from "./$types";
import { getHost } from "$lib/utils/get_host";

export const load: PageServerLoad = async () => {
    return {}
}

interface loginResponse {
    message: string,
    details?: string,
    user_data:{
        id: number,
        username: string,
        email: string,
        jwt: string,
        reset_jwt: string
    }
}

interface ErrorResponse{
    status: number,
    detail?: string,
}

export const actions = {
    login: async ({ request, cookies }) => {
        const backendUrl = env.URL_BACKEND ?? "http://back-dev:5000";
        const data = await request.formData();
        const username = data.get("username");
        const password = data.get("password");
        const response = await fetch(`${backendUrl}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-tenant-host": getHost(request),
            },
            body: JSON.stringify({ username, password }),
        });
        if (!response.ok) {
            try{
                const result:ErrorResponse = await response.json();
                return fail(response.status, { error: true, message: result.detail ?? "Login failed" });
            }
            catch(e){
                return fail(response.status, { error: true, message: "Internal Error" });
            }
            
        }
        const result: loginResponse = await response.json();
        //JWT is valid for 1 hour and JWT refresh token is valid for 24 hours, so we set the cookie to expire in 24 hours
        cookies.set("jwt", result.user_data.jwt, {path: "/", httpOnly: true, maxAge: 60 * 60});
        cookies.set("refresh_jwt", result.user_data.reset_jwt, {path: "/", httpOnly: true, maxAge: 60 * 60 * 24});
        return redirect(302, "/");
    },
    logout: async ({ cookies, request}) => {
        const backendUrl = env.URL_BACKEND ?? "http://back-dev:5000";
        const jwt = cookies.get("jwt");
        if (!jwt) {
            return redirect(302, "/");
        }
        await fetch(`${backendUrl}/auth/logout`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-tenant-host": getHost(request),
                "Authorization": `Bearer ${jwt}`
            },
        });
        cookies.delete("jwt", { path: "/" });
        cookies.delete("refresh_jwt", { path: "/" });
        return redirect(302, "/");
    },
    test: async ({ request }) => {
        const backendUrl = env.URL_BACKEND ?? "http://back-dev:5000";
        const response = await fetch(`${backendUrl}/auth/test`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-tenant-host": getHost(request),
            },
        });
        if (!response.ok) {
            return fail(response.status, { error: true, message: "Failed to test" });
        }
        const result = await response.json();
        console.log(result);
    }
} satisfies Actions;