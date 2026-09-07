import { Tabs } from 'expo-router';
import React from 'react';
import { Ionicons } from '@expo/vector-icons';

import { ConsultationProvider } from '@/consultation/ConsultationContext';
import { useLanguage } from '@/i18n/LanguageContext';

type TabIconProps = { color: string; size: number; focused: boolean };

export default function ConsultationLayout() {
  const { t } = useLanguage();

  return (
    <ConsultationProvider>
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarActiveTintColor: '#6F89B9',
          tabBarInactiveTintColor: '#A0AEC0',
          tabBarStyle: {
            height: 70,
            paddingTop: 8,
            paddingBottom: 8,
            backgroundColor: '#FFFFFF',
            borderTopWidth: 0,
            elevation: 8,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: -2 },
            shadowOpacity: 0.08,
            shadowRadius: 10,
          },
          tabBarLabelStyle: {
            fontSize: 11,
            fontWeight: '600',
            marginTop: 2,
          },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: t.tabs.home,
            tabBarIcon: ({ color, size, focused }: TabIconProps) => (
              <Ionicons
                name={focused ? 'calendar' : 'calendar-outline'}
                size={size}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="doctors"
          options={{
            title: t.tabs.doctors,
            tabBarIcon: ({ color, size, focused }: TabIconProps) => (
              <Ionicons
                name={focused ? 'people' : 'people-outline'}
                size={size}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="mycare"
          options={{
            title: t.tabs.myCare,
            tabBarIcon: ({ color, size, focused }: TabIconProps) => (
              <Ionicons
                name={focused ? 'heart' : 'heart-outline'}
                size={size}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="profile"
          options={{
            title: t.tabs.profile,
            tabBarIcon: ({ color, size, focused }: TabIconProps) => (
              <Ionicons
                name={focused ? 'person' : 'person-outline'}
                size={size}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen name="chat" options={{ href: null }} />
        <Tabs.Screen name="call" options={{ href: null }} />
      </Tabs>
    </ConsultationProvider>
  );
}
