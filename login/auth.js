/**
 * auth.js — client-side auth backed by localStorage.
 * users.json is fetched once on first visit to seed the store.
 * All subsequent reads/writes go through localStorage('scorates_users').
 */
const Auth = (() => {
  const STORE_KEY = 'scorates_users';
  const SESSION_KEY = 'scorates_session';

  // --- helpers ---

  function getUsers() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  function saveUsers(users) {
    localStorage.setItem(STORE_KEY, JSON.stringify(users));
  }

  function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  }

 
  function seedFromJSON() {
    if (getUsers() !== null) return; // already seeded
    fetch('users.json')
      .then(r => r.json())
      .then(data => {
        if (!getUsers()) saveUsers(data.users || []);
      })
      .catch(() => {
        if (!getUsers()) saveUsers([]);
      });
  }

  seedFromJSON();

  // --- public API ---

  function register(name, email, password) {
    const users = getUsers() || [];
    const normalEmail = email.trim().toLowerCase();

    if (users.find(u => u.email === normalEmail)) {
      return { success: false, message: 'An account with that email already exists.' };
    }

    const newUser = {
      id: generateId(),
      name: name.trim(),
      email: normalEmail,
      password: password   // plain-text; swap for a hash in a real backend
    };

    users.push(newUser);
    saveUsers(users);
    return { success: true };
  }

  function login(email, password) {
    const users = getUsers() || [];
    const normalEmail = email.trim().toLowerCase();
    const user = users.find(u => u.email === normalEmail && u.password === password);

    if (!user) return { success: false };

    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ id: user.id, name: user.name }));
    return { success: true };
  }

  function getSession() {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  function logout() {
    sessionStorage.removeItem(SESSION_KEY);
  }

  return { register, login, getSession, logout };
})();
