export const getHost = (request:Request) => {
    const host = request.headers.get("host") as string;
    return host
}