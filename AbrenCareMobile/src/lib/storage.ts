import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * Reads and parses a stored JSON value. Returns null when the key is missing
 * or the stored value is unreadable, so callers can fall back to their seed.
 */
export async function loadJson<T>(key: string): Promise<T | null> {
  try {
    const raw = await AsyncStorage.getItem(key);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

/** Writes a value without blocking the caller; storage errors are ignored. */
export function saveJson(key: string, value: unknown) {
  AsyncStorage.setItem(key, JSON.stringify(value)).catch(() => {
    // Ignore storage write errors (full disk, restricted profile).
  });
}
