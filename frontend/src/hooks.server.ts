import { env } from "$env/dynamic/private";
import type { Handle } from "@sveltejs/kit";

export const handle: Handle = async ({ event, resolve }) => {
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
    console.log("admin_mode:", admin_mode, "jwt:", jwt, "refreshToken:", refreshToken);

    if (!jwt && refreshToken) {
        try {
            const backendUrl = env.URL_BACKEND;
            
            const response = await fetch(`${backendUrl}${admin_mode?"/admin":""}/auth/refresh`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
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
            }

        } catch (err) {
            console.error("error en refresh:", err);
        }
    }

    return resolve(event);
};