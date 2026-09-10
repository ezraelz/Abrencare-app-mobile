import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useColorScheme } from 'react-native';

import { AuthProvider } from '@/auth/AuthContext';
import { AnimatedSplashOverlay } from '@/components/animated-icon';
import { AppointmentsProvider } from '@/family/AppointmentsContext';
import { ReminderWatcher } from '@/family/ReminderWatcher';
import { LanguageProvider } from '@/i18n/LanguageContext';
import { ChatProvider } from '@/contexts/ChatContext';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
    <LanguageProvider>
      <AuthProvider>
        <ChatProvider>
          <AppointmentsProvider>
            <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
              <AnimatedSplashOverlay />
              <ReminderWatcher />
              <Stack screenOptions={{ headerShown: false }} />
            </ThemeProvider>
          </AppointmentsProvider>
        </ChatProvider>
      </AuthProvider>
    </LanguageProvider>
  );
}
