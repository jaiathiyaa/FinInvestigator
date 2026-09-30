import axios from "axios";

const api = axios.create({
    baseURL: "http://localhost:8000"
})

export async function investigate(query: string) {
    const response = await api.post("/api/investigations",{
        query
    });

    return response.data;
}