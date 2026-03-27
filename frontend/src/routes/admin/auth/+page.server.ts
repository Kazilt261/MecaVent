import { fail, redirect, type Actions } from "@sveltejs/kit";
import { env } from "$env/dynamic/private";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async () => {
    return {}
}

interface loginResponse {
    message: string,
    user_data:{
        id: number,
        username: string,
        email: string,
        jwt: string,
        reset_jwt: string
    }
}

export const actions = {
    login: async ({ request, cookies }) => {
        const backendUrl = (env.URL_BACKEND ?? "http://back-dev:5000") + "/admin";
        const data = await request.formData();
        const username = data.get("username");
        const password = data.get("password");
        const response = await fetch(`${backendUrl}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });
        if (!response.ok) {
            return fail(response.status, { error: true, message: "Failed to sign in" });
        }
        const result: loginResponse = await response.json();
        //JWT is valid for 1 hour and JWT refresh token is valid for 24 hours, so we set the cookie to expire in 24 hours
        cookies.set("jwt_admin", result.user_data.jwt, {path: "/", httpOnly: true, maxAge: 60 * 60});
        cookies.set("refresh_jwt_admin", result.user_data.reset_jwt, {path: "/", httpOnly: true, maxAge: 60 * 60 * 24});
        return redirect(302, "/admin");
    },
    logout: async ({ cookies }) => {
        const backendUrl = (env.URL_BACKEND ?? "http://back-dev:5000") + "/admin";
        const jwt = cookies.get("jwt_admin");
        if (!jwt) {
            return redirect(302, "/admin");
        }
        await fetch(`${backendUrl}/auth/logout`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${jwt}`
            },
        });
        cookies.delete("jwt_admin", { path: "/" });
        cookies.delete("reset_jwt_admin", { path: "/" });
        return redirect(302, "/admin");
    }
} satisfies Actions;