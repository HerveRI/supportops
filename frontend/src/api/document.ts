const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export interface Document {
    id: string;
    original_filename: string;
    content_type: string;
    file_size_bytes: number;
    uploaded_by_user_id: string;
    created_at: string;
}

async function getErrorDetail(response: Response): Promise<string> {
    try{
        const body = (await response.json()) as { detail?: string};
        return body.detail ?? "Request failed";
    } catch {
        return "Request failed";
    }
}

export async function uploadDocument(file:File): Promise<Document> {
    const formData = new FormData();
    
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/admin/documents`, {
        method: "POST",
        credentials: "include",
        body: formData,
    });

    if(!response.ok) {
        throw new Error(await getErrorDetail(response));
    }

    return response.json() as Promise<Document>;
}