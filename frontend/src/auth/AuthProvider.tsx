import { useEffect, useState, type ReactNode } from "react";

import {
    getCurrentUser,
    loginRequest,
    logoutRequest,
    signupRequest,
    type User,
} from "../api/auth";
import { AuthContext } from "./AuthContext";

interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;

        async function loadCurrentUser() {
            try {
                const currentUser = await getCurrentUser();

                if (isMounted) {
                    setUser(currentUser);
                }
            } catch (error) {
                console.error("Failed to load current user:", error);
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }

        void loadCurrentUser();

        return () => {
            isMounted = false;
        };
    }, []);

    async function login(email: string, password: string) {
        const loggedInUser = await loginRequest(email, password);
        setUser(loggedInUser);
    }

    async function signup(email: string, password: string) {
        await signupRequest(email, password);
    }

    async function logout() {
        await logoutRequest();
        setUser(null);
    }

    return (
        <AuthContext.Provider value={{
            user,
            isLoading,
            login,
            signup,
            logout,
        }}>
            {children}
        </AuthContext.Provider>
    );
}

