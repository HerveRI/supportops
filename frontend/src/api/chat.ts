export interface ChatCitation {
    citation_number: number;
    chunk_id: string;
    document_id: string;
    original_filename: string;
    chunk_index: number;
    text: string;
    page_number: number | null;
}

export interface ChatResponse {
    answer: string;
    citations: ChatCitation[];
}

export async function sendChatMessage(
    question: string,
): Promise<ChatResponse> {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

    const response = await fetch(`${apiBaseUrl}/chat`,{
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
    });

    if(!response.ok) {
        let message = "Chat request failed";

        try {
            const data = await response.json();

            if (typeof data.detail === "string") {
                message = data.detail;
            }
        } catch {
            // Kee the fallback message when the response body is not JSON.
        }

        throw new Error(message);
    }

    return response.json();

}