const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

if(!API_BASE_URL) {
    throw new Error("VITE_API_BASE_URL is not configured");
}

export type UserRole = "member" | "admin";

export interface User {
    id: string;
    email: string;
    role: UserRole;
    is_active: boolean;
    created_at: string;
    update_at: string;
}

async function getErrorMessage(response: Response): Promise<string>{
    try {
        const data = (await response.json()) as {detail?: unknown};
        
        if (typeof data.detail === "string") {
            return data.detail;
        }

    } catch {
        // The response body was not valid JSON
    }
    

    return `Request failed with status ${response.status}`;
}

export async function getCurrentUser(): Promise<User | null> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: "GET",
        credentials: "include",
    });

    if (response.status === 401) {
        return null;
    }

    if (!response.ok) {
        throw new Error (await getErrorMessage(response));
    }

    return (await response.json()) as User;
}

export async function signupRequest(
    email: string,
    password: string,
): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/signup`,{
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            email,
            password,
        }),
    });

    if(!response.ok) {
        throw new Error(await getErrorMessage(response));
    }

    return (await response.json()) as User;
}

export async function loginRequest(
    email: string,
    password: string,
): Promise<User>{
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            email, 
            password,
        }),
    });

    if (!response.ok) {
        throw new Error(await getErrorMessage(response));
    }

    return (await response.json()) as User;
}

export async function logoutRequest(): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        throw new Error(await getErrorMessage(response));
    }
}