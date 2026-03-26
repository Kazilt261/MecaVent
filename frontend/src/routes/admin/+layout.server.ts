import { env } from "$env/dynamic/private";
import { redirect } from "@sveltejs/kit";
import type { LayoutServerLoad } from "../$types";

export const load: LayoutServerLoad = async ({ depends, cookies, locals }) => {
    depends("app:admin/auth");
    const jwt = cookies.get("jwt_admin");
    const jwt_refresh = cookies.get("refresh_jwt_admin");

    if (!jwt && !jwt_refresh) {
        return {};
    }
    console.log("Admin JWT found, validating...");
    const response = await fetch(
        `${env.URL_BACKEND ?? "http://back-dev:5000"}/admin/auth`,
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${jwt}`
            },
        }
    )
    if (!response.ok) {
        cookies.delete("jwt_admin", { path: "/" });
        cookies.delete("refresh_jwt_admin", { path: "/" });
        return {};
    }
    const user = await response.json();

    return {
        user: user
    };
}