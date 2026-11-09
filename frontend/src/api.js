import axios from "axios";

const API = axios.create({
  baseURL: "https://shelving-washtub-buzz.ngrok-free.dev",
  headers: {
    "ngrok-skip-browser-warning": "true",
  },
});

// Create New Conversation
export const createConversation = async () => {
  const response = await API.post("/conversations");
  return response.data;
};

// Get All Conversations
export const getConversations = async () => {
  const response = await API.get("/conversations");
  return response.data;
};

// Get Conversation History
export const getConversationHistory = async (id) => {
  const response = await API.get(`/conversations/${id}/messages`);
  return response.data;
};

// Upload PDF
export const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await API.post("/upload-pdf", formData);
  return response.data;
};

// Send Chat Message
export const sendMessage = async (conversationId, question) => {
  const response = await API.post("/chat", {
    conversation_id: conversationId,
    question: question,
  });

  return response.data;
};

export default API;
