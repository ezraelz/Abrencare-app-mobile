import { useState } from 'react';
import {
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthContext';
import { serviceThemes } from '@/auth/serviceTheme';
import type { FamilyMember, FamilyMemberKind } from '@/auth/types';
import AuthScaffold from '@/components/auth/AuthScaffold';
import Replace from '@/components/Replace';
import { useLanguage } from '@/i18n/LanguageContext';

const OPTIONS: {
  kind: FamilyMemberKind;
  icon: keyof typeof Ionicons.glyphMap;
  labelKey: 'addChild' | 'addSpouse' | 'addParent' | 'addMember';
}[] = [
  { kind: 'child', icon: 'happy-outline', labelKey: 'addChild' },
  { kind: 'spouse', icon: 'heart-outline', labelKey: 'addSpouse' },
  { kind: 'parent', icon: 'people-outline', labelKey: 'addParent' },
  { kind: 'member', icon: 'person-add-outline', labelKey: 'addMember' },
];

export default function FamilySetupScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const { user, completeFamilyOnboarding, hasService } = useAuth();
  const theme = serviceThemes.family;

  const [members, setMembers] = useState<FamilyMember[]>(
    user?.familyMembers ?? [],
  );
  const [adding, setAdding] = useState<FamilyMemberKind | null>(null);
  const [name, setName] = useState('');

  if (!user || !hasService('family')) {
    return <Replace href="/signup?service=family" />;
  }

  function addMember(kind: FamilyMemberKind, memberName: string) {
    const created: FamilyMember = {
      id: `member-${Date.now()}`,
      kind,
      name: memberName.trim(),
    };
    setMembers((current) => [...current, created]);
    setAdding(null);
    setName('');
  }

  function removeMember(id: string) {
    setMembers((current) => current.filter((member) => member.id !== id));
  }

  const addingLabel = OPTIONS.find((option) => option.kind === adding);

  return (
    <AuthScaffold
      theme={theme}
      serviceLabel={t.familySignup.service}
      title={t.familySignup.welcomeTitle}
      subtitle={`${t.familySignup.setupTitle}\n${t.familySignup.setupSubtitle}`}
    >
      <View style={styles.optionList}>
        {OPTIONS.map((option) => (
          <Pressable
            key={option.kind}
            style={({ pressed }) => [
              styles.option,
              { borderColor: theme.border, backgroundColor: theme.card },
              pressed && styles.pressed,
            ]}
            onPress={() => {
              setAdding(option.kind);
              setName('');
            }}
          >
            <View style={[styles.optionIcon, { backgroundColor: theme.accentSoft }]}>
              <Ionicons name={option.icon} size={18} color={theme.accent} />
            </View>
            <Text style={[styles.optionText, { color: theme.text }]}>
              + {t.familySignup[option.labelKey]}
            </Text>
            <Ionicons name="add" size={18} color={theme.accent} />
          </Pressable>
        ))}
      </View>

      {members.length > 0 && (
        <View style={styles.added}>
          {members.map((member) => (
            <View
              key={member.id}
              style={[styles.chip, { backgroundColor: theme.accentSoft }]}
            >
              <Text style={[styles.chipText, { color: theme.text }]}>
                {member.name || t.familySignup[labelForKind(member.kind)]}
              </Text>
              <Pressable onPress={() => removeMember(member.id)} hitSlop={8}>
                <Ionicons name="close" size={14} color={theme.muted} />
              </Pressable>
            </View>
          ))}
        </View>
      )}

      <Pressable
        style={({ pressed }) => [
          styles.button,
          { backgroundColor: theme.accent },
          pressed && styles.pressed,
        ]}
        onPress={() => {
          completeFamilyOnboarding(members);
          router.replace('/family');
        }}
      >
        <Text style={styles.buttonText}>{t.auth.continue}</Text>
      </Pressable>

      <Modal
        visible={adding !== null}
        transparent
        animationType="fade"
        onRequestClose={() => setAdding(null)}
      >
        <Pressable style={styles.backdrop} onPress={() => setAdding(null)}>
          <Pressable style={styles.sheet}>
            <Text style={styles.sheetTitle}>
              {addingLabel
                ? t.familySignup[addingLabel.labelKey]
                : t.familySignup.addMember}
            </Text>
            <Text style={styles.sheetLabel}>{t.familySignup.memberName}</Text>
            <TextInput
              value={name}
              onChangeText={setName}
              placeholder={t.familySignup.memberPlaceholder}
              placeholderTextColor="#A8AEB4"
              autoCapitalize="words"
              style={styles.sheetInput}
            />
            <Pressable
              style={[styles.sheetButton, { backgroundColor: theme.accent }]}
              onPress={() => adding && addMember(adding, name)}
            >
              <Text style={styles.buttonText}>
                {name.trim() ? t.familySignup.add : t.familySignup.skipName}
              </Text>
            </Pressable>
            <Pressable onPress={() => setAdding(null)} style={styles.cancel}>
              <Text style={styles.cancelText}>{t.familySignup.cancel}</Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>
    </AuthScaffold>
  );
}

function labelForKind(kind: FamilyMemberKind) {
  if (kind === 'child') {
    return 'addChild' as const;
  }
  if (kind === 'spouse') {
    return 'addSpouse' as const;
  }
  if (kind === 'parent') {
    return 'addParent' as const;
  }
  return 'addMember' as const;
}

const styles = StyleSheet.create({
  optionList: {
    gap: 10,
    marginBottom: 18,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 14,
    minHeight: 58,
  },
  optionIcon: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  optionText: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
  },
  added: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 20,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  chipText: {
    fontSize: 13,
    fontWeight: '600',
  },
  button: {
    height: 54,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  pressed: {
    opacity: 0.88,
  },
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(20, 24, 30, 0.4)',
    justifyContent: 'center',
    paddingHorizontal: 28,
  },
  sheet: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 20,
  },
  sheetTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#2F3A2F',
    marginBottom: 14,
  },
  sheetLabel: {
    fontSize: 12,
    color: '#6F7F73',
    marginBottom: 8,
  },
  sheetInput: {
    borderWidth: 1,
    borderColor: '#E2E6DE',
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 48,
    fontSize: 15,
    marginBottom: 14,
  },
  sheetButton: {
    height: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancel: {
    alignItems: 'center',
    paddingTop: 14,
  },
  cancelText: {
    fontSize: 14,
    color: '#6F7F73',
    fontWeight: '600',
  },
});
