import { defineStore } from "pinia";
import { ref } from "vue";
import { http } from "../api/http";

interface User {
  user_id: string;
  username: string;
  display_name: string;
  role_code: string;
}

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const token = ref(localStorage.getItem("token") || "");

  if (token.value) {
    http.defaults.headers.common["Authorization"] = `Bearer ${token.value}`;
  }

  async function login(username: string, password: string): Promise<void> {
    const { data } = await http.post<{
      token: string; username: string; display_name: string; role_code: string;
    }>("/auth/login", { username, password });
    token.value = data.token;
    localStorage.setItem("token", data.token);
    http.defaults.headers.common["Authorization"] = `Bearer ${data.token}`;
    user.value = {
      user_id: "",
      username: data.username,
      display_name: data.display_name,
      role_code: data.role_code,
    };
  }

  async function loadUser(): Promise<void> {
    try {
      const { data } = await http.get<User>("/auth/me");
      user.value = data;
    } catch {
      logout();
    }
  }

  function logout(): void {
    token.value = "";
    user.value = null;
    localStorage.removeItem("token");
    delete http.defaults.headers.common["Authorization"];
  }

  const isLoggedIn = () => !!token.value;
  const isAdmin = () => user.value?.role_code === "admin";

  return { user, token, login, logout, loadUser, isLoggedIn, isAdmin };
});
