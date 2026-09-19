import { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type KeyboardTypeOptions,
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';

import type { ServiceTheme } from '@/auth/serviceTheme';

type Props = {
  theme: ServiceTheme;
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  icon: keyof typeof Ionicons.glyphMap;
  secure?: boolean;
  keyboardType?: KeyboardTypeOptions;
  autoCapitalize?: 'none' | 'words' | 'sentences';
};

export default function AuthField({
  theme,
  label,
  value,
  onChangeText,
  placeholder,
  icon,
  secure,
  keyboardType,
  autoCapitalize = 'none',
}: Props) {
  const [visible, setVisible] = useState(false);

  return (
    <View style={styles.wrap}>
      <Text style={[styles.label, { color: theme.muted }]}>{label}</Text>
      <View
        style={[
          styles.field,
          {
            backgroundColor: theme.field,
            borderColor: theme.border,
          },
        ]}
      >
        <Ionicons
          name={icon}
          size={18}
          color={theme.accent}
          style={styles.icon}
        />
        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor="#A8AEB4"
          secureTextEntry={Boolean(secure) && !visible}
          autoCapitalize={autoCapitalize}
          autoCorrect={false}
          keyboardType={keyboardType}
          style={[styles.input, { color: theme.text }]}
        />
        {secure && (
          <Pressable onPress={() => setVisible((current) => !current)} hitSlop={10}>
            <Ionicons
              name={visible ? 'eye-off-outline' : 'eye-outline'}
              size={18}
              color="#9AA3AF"
            />
          </Pressable>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    marginBottom: 14,
  },
  label: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.1,
    marginBottom: 8,
  },
  field: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 14,
    borderWidth: 1,
    minHeight: 54,
    paddingHorizontal: 12,
  },
  icon: {
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 15,
    paddingVertical: 14,
  },
});
