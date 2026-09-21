import { useState } from 'react';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthContext';
import { serviceThemes } from '@/auth/serviceTheme';
import {
  kindFromRelationship,
  type FamilyCareNeed,
  type FamilyMember,
  type FamilyRelationship,
} from '@/auth/types';
import Replace from '@/components/Replace';
import { useLanguage } from '@/i18n/LanguageContext';

type Draft = {
  name: string;
  relationship: FamilyRelationship | null;
  dateOfBirth: string;
  phone: string;
  city: string;
  address: string;
  emergencyPhone: string;
  careNeed: FamilyCareNeed | null;
  preferredLanguage: 'en' | 'am' | '';
  notes: string;
};

const emptyDraft = (): Draft => ({
  name: '',
  relationship: null,
  dateOfBirth: '',
  phone: '',
  city: '',
  address: '',
  emergencyPhone: '',
  careNeed: null,
  preferredLanguage: '',
  notes: '',
});

export default function FamilySetupScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const { user, hasService, setFamilyMembers, completeFamilyOnboarding } =
    useAuth();
  const theme = serviceThemes.family;
  const copy = t.familyAdd;

  const [members, setMembers] = useState<FamilyMember[]>(
    user?.familyMembers ?? [],
  );
  const [step, setStep] = useState<0 | 1 | 2 | 3 | 4>(0);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [confirmed, setConfirmed] = useState(false);
  const [openMenu, setOpenMenu] = useState<'relationship' | 'language' | null>(
    null,
  );

  const relationships: { id: FamilyRelationship; label: string }[] = [
    { id: 'mother', label: copy.mother },
    { id: 'father', label: copy.father },
    { id: 'parent', label: copy.parent },
    { id: 'spouse', label: copy.spouse },
    { id: 'child', label: copy.child },
    { id: 'other', label: copy.other },
  ];

  const careNeeds: { id: FamilyCareNeed; label: string }[] = [
    { id: 'homeVisits', label: copy.homeVisits },
    { id: 'vitals', label: copy.vitals },
    { id: 'medication', label: copy.medication },
    { id: 'labs', label: copy.labs },
    { id: 'doctor', label: copy.doctor },
    { id: 'general', label: copy.general },
  ];

  if (!user || !hasService('family')) {
    return <Replace href="/signup?service=family" />;
  }

  const canStep1 = draft.name.trim().length > 1 && draft.relationship !== null;
  const canStep2 = draft.phone.trim().length >= 8 && draft.city.trim().length > 1;
  const relationshipLabel = relationships.find(
    (item) => item.id === draft.relationship,
  )?.label;
  const careLabel = careNeeds.find((item) => item.id === draft.careNeed)?.label;

  function startAdd() {
    setDraft(emptyDraft());
    setConfirmed(false);
    setOpenMenu(null);
    setStep(1);
  }

  function saveMember() {
    if (!draft.relationship || !confirmed) {
      return;
    }

    const created: FamilyMember = {
      id: `member-${Date.now()}`,
      kind: kindFromRelationship(draft.relationship),
      name: draft.name.trim(),
      relationship: draft.relationship,
      dateOfBirth: draft.dateOfBirth.trim(),
      phone: draft.phone.trim(),
      city: draft.city.trim(),
      address: draft.address.trim(),
      emergencyPhone: draft.emergencyPhone.trim(),
      careNeed: draft.careNeed,
      preferredLanguage: draft.preferredLanguage,
      notes: draft.notes.trim(),
      status: 'active',
    };

    const next = [...members, created];
    setMembers(next);
    setFamilyMembers(next);
    setStep(0);
  }

  function goDashboard() {
    completeFamilyOnboarding(members);
    router.replace('/family');
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.background }]}>
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.card}>
          {step === 0 ? (
            <Overview
              members={members}
              copy={copy}
              theme={theme}
              onAdd={startAdd}
              onContinue={goDashboard}
            />
          ) : (
            <Wizard
              step={step}
              draft={draft}
              setDraft={setDraft}
              confirmed={confirmed}
              setConfirmed={setConfirmed}
              openMenu={openMenu}
              setOpenMenu={setOpenMenu}
              relationships={relationships}
              careNeeds={careNeeds}
              relationshipLabel={relationshipLabel}
              careLabel={careLabel}
              canStep1={canStep1}
              canStep2={canStep2}
              copy={copy}
              theme={theme}
              onBack={() => {
                if (step === 1) {
                  setStep(0);
                  return;
                }
                setStep((current) => (current - 1) as 1 | 2 | 3 | 4);
              }}
              onContinue={() => {
                if (step === 4) {
                  saveMember();
                  return;
                }
                setStep((current) => (current + 1) as 1 | 2 | 3 | 4);
              }}
            />
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function Overview({
  members,
  copy,
  theme,
  onAdd,
  onContinue,
}: {
  members: FamilyMember[];
  copy: ReturnType<typeof useLanguage>['t']['familyAdd'];
  theme: typeof serviceThemes.family;
  onAdd: () => void;
  onContinue: () => void;
}) {
  return (
    <View>
      <Text style={[styles.kicker, { color: theme.accent }]}>{copy.kicker}</Text>
      <View style={styles.titleRow}>
        <View style={styles.flex}>
          <Text style={[styles.title, { color: theme.text }]}>{copy.title}</Text>
          <Text style={[styles.subtitle, { color: theme.muted }]}>
            {copy.subtitle}
          </Text>
        </View>
        <View style={[styles.peopleMark, { backgroundColor: theme.accentSoft }]}>
          <Ionicons name="people-outline" size={20} color={theme.accent} />
        </View>
      </View>

      {members.length === 0 ? (
        <>
          <View style={styles.placeholderCard}>
            <View style={styles.placeholderLeft}>
              <View style={[styles.avatar, { backgroundColor: theme.accentSoft }]}>
                <Ionicons name="person-outline" size={16} color={theme.accent} />
              </View>
              <View>
                <Text style={[styles.memberName, { color: theme.text }]}>
                  {copy.placeholderName}
                </Text>
                <Text style={[styles.memberMeta, { color: theme.muted }]}>
                  {copy.notAdded}
                </Text>
              </View>
            </View>
            <View style={[styles.badge, { backgroundColor: theme.accentSoft }]}>
              <Text style={[styles.badgeText, { color: theme.accent }]}>
                {copy.newBadge}
              </Text>
            </View>
          </View>
          <View style={styles.hintRow}>
            <Ionicons name="heart-outline" size={14} color={theme.accent} />
            <Text style={[styles.hint, { color: theme.muted }]}>{copy.hint}</Text>
          </View>
        </>
      ) : (
        <View style={styles.list}>
          <Text style={[styles.listTitle, { color: theme.text }]}>
            {copy.membersTitle}
          </Text>
          {members.map((member) => (
            <View key={member.id} style={styles.memberRow}>
              <View style={[styles.avatar, { backgroundColor: theme.accentSoft }]}>
                <Ionicons name="person-outline" size={16} color={theme.accent} />
              </View>
              <View style={styles.flex}>
                <Text style={[styles.memberName, { color: theme.text }]}>
                  {member.name}
                </Text>
                <Text style={[styles.memberMeta, { color: theme.muted }]}>
                  {copy.careProfile} ·{' '}
                  {member.status === 'active' ? copy.active : copy.notAdded}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      <View style={[styles.dashed, { borderColor: theme.accent }]}>
        <View style={[styles.plus, { backgroundColor: theme.accentSoft }]}>
          <Ionicons name="add" size={22} color={theme.accent} />
        </View>
        <Text style={[styles.dashedTitle, { color: theme.text }]}>
          {members.length === 0 ? copy.addParent : copy.addAnother}
        </Text>
        {members.length === 0 && (
          <Text style={[styles.dashedBody, { color: theme.muted }]}>
            {copy.addParentBody}
          </Text>
        )}
        <Pressable
          style={({ pressed }) => [
            styles.addButton,
            { backgroundColor: theme.accent },
            pressed && styles.pressed,
          ]}
          onPress={onAdd}
        >
          <Text style={styles.addButtonText}>
            {members.length === 0 ? copy.addMember : copy.addAnother}
          </Text>
        </Pressable>
      </View>

      <View style={styles.privacy}>
        <Ionicons name="lock-closed-outline" size={13} color={theme.muted} />
        <Text style={[styles.privacyText, { color: theme.muted }]}>
          {copy.privacy}
        </Text>
      </View>

      {members.length > 0 && (
        <Pressable
          style={({ pressed }) => [
            styles.continue,
            { backgroundColor: theme.accent },
            pressed && styles.pressed,
          ]}
          onPress={onContinue}
        >
          <Text style={styles.addButtonText}>{copy.continue}</Text>
        </Pressable>
      )}
    </View>
  );
}

function Wizard({
  step,
  draft,
  setDraft,
  confirmed,
  setConfirmed,
  openMenu,
  setOpenMenu,
  relationships,
  careNeeds,
  relationshipLabel,
  careLabel,
  canStep1,
  canStep2,
  copy,
  theme,
  onBack,
  onContinue,
}: {
  step: 1 | 2 | 3 | 4;
  draft: Draft;
  setDraft: (value: Draft | ((current: Draft) => Draft)) => void;
  confirmed: boolean;
  setConfirmed: (value: boolean) => void;
  openMenu: 'relationship' | 'language' | null;
  setOpenMenu: (value: 'relationship' | 'language' | null) => void;
  relationships: { id: FamilyRelationship; label: string }[];
  careNeeds: { id: FamilyCareNeed; label: string }[];
  relationshipLabel?: string;
  careLabel?: string;
  canStep1: boolean;
  canStep2: boolean;
  copy: ReturnType<typeof useLanguage>['t']['familyAdd'];
  theme: typeof serviceThemes.family;
  onBack: () => void;
  onContinue: () => void;
}) {
  const titles = [copy.basicTitle, copy.contactTitle, copy.careTitle, copy.reviewTitle];
  const canGo =
    step === 1 ? canStep1 : step === 2 ? canStep2 : step === 4 ? confirmed : true;

  const languageLabel =
    draft.preferredLanguage === 'en'
      ? tEnglish
      : draft.preferredLanguage === 'am'
        ? tAmharic
        : copy.languagePlaceholder;

  return (
    <View>
      <View style={styles.wizardHeader}>
        <Text style={[styles.formKicker, { color: theme.muted }]}>
          {copy.formKicker}
        </Text>
        <Text style={[styles.stepCount, { color: theme.muted }]}>
          {step} {copy.stepOf} 4
        </Text>
      </View>
      <Text style={[styles.title, { color: theme.text }]}>{titles[step - 1]}</Text>

      <View style={styles.progress}>
        {[1, 2, 3, 4].map((item) => (
          <View
            key={item}
            style={[
              styles.progressSeg,
              {
                backgroundColor:
                  item <= step ? theme.accent : 'rgba(110, 139, 116, 0.18)',
              },
            ]}
          />
        ))}
      </View>

      {step === 1 && (
        <View>
          <View style={[styles.infoBox, { backgroundColor: theme.accentSoft }]}>
            <Ionicons name="person-outline" size={16} color={theme.accent} />
            <View style={styles.flex}>
              <Text style={[styles.infoTitle, { color: theme.text }]}>
                {copy.whoTitle}
              </Text>
              <Text style={[styles.infoBody, { color: theme.muted }]}>
                {copy.whoSubtitle}
              </Text>
            </View>
          </View>
          <Field
            label={copy.fullName}
            value={draft.name}
            onChangeText={(name) => setDraft((current) => ({ ...current, name }))}
            placeholder={copy.fullNamePlaceholder}
          />
          <Select
            label={copy.relationship}
            value={relationshipLabel ?? copy.relationshipPlaceholder}
            filled={Boolean(draft.relationship)}
            open={openMenu === 'relationship'}
            onToggle={() =>
              setOpenMenu(openMenu === 'relationship' ? null : 'relationship')
            }
            options={relationships.map((item) => item.label)}
            onSelect={(label) => {
              const match = relationships.find((item) => item.label === label);
              if (match) {
                setDraft((current) => ({ ...current, relationship: match.id }));
              }
              setOpenMenu(null);
            }}
          />
          <Field
            label={copy.dob}
            value={draft.dateOfBirth}
            onChangeText={(dateOfBirth) =>
              setDraft((current) => ({ ...current, dateOfBirth }))
            }
            placeholder={copy.dobPlaceholder}
          />
        </View>
      )}

      {step === 2 && (
        <View>
          <Field
            label={copy.phone}
            value={draft.phone}
            onChangeText={(phone) => setDraft((current) => ({ ...current, phone }))}
            placeholder={copy.phonePlaceholder}
            keyboardType="phone-pad"
          />
          <Field
            label={copy.city}
            value={draft.city}
            onChangeText={(city) => setDraft((current) => ({ ...current, city }))}
            placeholder={copy.cityPlaceholder}
          />
          <Field
            label={copy.address}
            value={draft.address}
            onChangeText={(address) =>
              setDraft((current) => ({ ...current, address }))
            }
            placeholder={copy.addressPlaceholder}
            multiline
          />
          <Field
            label={copy.emergency}
            value={draft.emergencyPhone}
            onChangeText={(emergencyPhone) =>
              setDraft((current) => ({ ...current, emergencyPhone }))
            }
            placeholder={copy.emergencyPlaceholder}
            keyboardType="phone-pad"
          />
        </View>
      )}

      {step === 3 && (
        <View>
          <Text style={styles.careIntro}>{copy.careSubtitle}</Text>
          {careNeeds.map((need) => (
            <Pressable
              key={need.id}
              style={styles.radioRow}
              onPress={() =>
                setDraft((current) => ({ ...current, careNeed: need.id }))
              }
            >
              <View
                style={[
                  styles.radio,
                  draft.careNeed === need.id && {
                    borderColor: theme.accent,
                    backgroundColor: theme.accent,
                  },
                ]}
              />
              <Text style={[styles.radioLabel, { color: theme.text }]}>
                {need.label}
              </Text>
            </Pressable>
          ))}
          <Select
            label={copy.language}
            value={languageLabel}
            filled={Boolean(draft.preferredLanguage)}
            open={openMenu === 'language'}
            onToggle={() =>
              setOpenMenu(openMenu === 'language' ? null : 'language')
            }
            options={[tEnglish, tAmharic]}
            onSelect={(label) => {
              setDraft((current) => ({
                ...current,
                preferredLanguage: label === tAmharic ? 'am' : 'en',
              }));
              setOpenMenu(null);
            }}
          />
          <Field
            label={copy.notes}
            value={draft.notes}
            onChangeText={(notes) => setDraft((current) => ({ ...current, notes }))}
            placeholder={copy.notesPlaceholder}
            multiline
          />
        </View>
      )}

      {step === 4 && (
        <View>
          <View style={[styles.review, { backgroundColor: theme.accentSoft }]}>
            <View style={styles.reviewHead}>
              <Ionicons name="person-outline" size={16} color={theme.accent} />
              <Text style={[styles.reviewName, { color: theme.text }]}>
                {draft.name}
              </Text>
            </View>
            <ReviewRow
              label={copy.reviewRelationship}
              value={relationshipLabel ?? copy.noneSelected}
            />
            <ReviewRow label={copy.reviewPhone} value={draft.phone} />
            <ReviewRow
              label={copy.reviewLocation}
              value={draft.city || copy.noneSelected}
            />
            <ReviewRow
              label={copy.reviewCare}
              value={careLabel ?? copy.noneSelected}
            />
          </View>

          <Pressable
            style={styles.confirmRow}
            onPress={() => setConfirmed(!confirmed)}
          >
            <View
              style={[
                styles.checkbox,
                { borderColor: theme.accent },
                confirmed && { backgroundColor: theme.accent },
              ]}
            >
              {confirmed && <Ionicons name="checkmark" size={14} color="#FFFFFF" />}
            </View>
            <Text style={[styles.confirmText, { color: theme.text }]}>
              {copy.confirm}
            </Text>
          </Pressable>
          <Text style={[styles.verify, { color: theme.muted }]}>{copy.verify}</Text>
        </View>
      )}

      <View style={styles.actions}>
        <Pressable style={styles.backBtn} onPress={onBack}>
          <Text style={[styles.backText, { color: theme.text }]}>{copy.back}</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [
            styles.nextBtn,
            { backgroundColor: canGo ? theme.accent : '#C5CBBE' },
            pressed && canGo && styles.pressed,
          ]}
          disabled={!canGo}
          onPress={onContinue}
        >
          <Text style={styles.addButtonText}>
            {step === 4 ? copy.save : copy.continueStep}
          </Text>
          {step !== 4 && <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />}
        </Pressable>
      </View>
    </View>
  );
}

const tEnglish = 'English';
const tAmharic = 'አማርኛ';

function Field({
  label,
  value,
  onChangeText,
  placeholder,
  keyboardType,
  multiline,
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  keyboardType?: 'phone-pad';
  multiline?: boolean;
}) {
  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor="#A8AEB4"
        keyboardType={keyboardType}
        multiline={multiline}
        style={[styles.input, multiline && styles.textarea]}
      />
    </View>
  );
}

function Select({
  label,
  value,
  filled,
  open,
  onToggle,
  options,
  onSelect,
}: {
  label: string;
  value: string;
  filled: boolean;
  open: boolean;
  onToggle: () => void;
  options: string[];
  onSelect: (value: string) => void;
}) {
  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <Pressable style={styles.select} onPress={onToggle}>
        <Text style={[styles.selectText, !filled && styles.placeholderText]}>
          {value}
        </Text>
        <Ionicons name="chevron-down" size={16} color="#6F6A64" />
      </Pressable>
      {open && (
        <View style={styles.menu}>
          {options.map((option) => (
            <Pressable
              key={option}
              style={styles.menuItem}
              onPress={() => onSelect(option)}
            >
              <Text style={styles.menuText}>{option}</Text>
            </Pressable>
          ))}
        </View>
      )}
    </View>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.reviewRow}>
      <Text style={styles.reviewLabel}>{label}</Text>
      <Text style={styles.reviewValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: {
    padding: 18,
    paddingBottom: 40,
    maxWidth: 640,
    width: '100%',
    alignSelf: 'center',
  },
  card: {
    backgroundColor: '#F6F2EA',
    borderRadius: 24,
    padding: 22,
  },
  kicker: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.4,
    marginBottom: 10,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 18,
  },
  flex: { flex: 1 },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  peopleMark: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 12,
  },
  placeholderCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  placeholderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  memberName: {
    fontSize: 15,
    fontWeight: '700',
  },
  memberMeta: {
    fontSize: 12,
    marginTop: 2,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  hintRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 18,
  },
  hint: {
    fontSize: 13,
  },
  list: {
    marginBottom: 16,
  },
  listTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 10,
  },
  memberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 12,
    marginBottom: 8,
  },
  dashed: {
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderRadius: 18,
    padding: 22,
    alignItems: 'center',
    marginBottom: 16,
  },
  plus: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  dashedTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 6,
  },
  dashedBody: {
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 19,
    marginBottom: 14,
  },
  addButton: {
    height: 44,
    paddingHorizontal: 22,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  privacy: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  privacyText: {
    fontSize: 12,
  },
  continue: {
    height: 50,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 18,
  },
  pressed: { opacity: 0.88 },
  wizardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  formKicker: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  stepCount: {
    fontSize: 12,
    fontWeight: '600',
  },
  progress: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 20,
    marginTop: 8,
  },
  progressSeg: {
    flex: 1,
    height: 4,
    borderRadius: 4,
  },
  infoBox: {
    flexDirection: 'row',
    gap: 10,
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
  },
  infoTitle: {
    fontSize: 15,
    fontWeight: '700',
  },
  infoBody: {
    fontSize: 13,
    marginTop: 2,
  },
  fieldWrap: {
    marginBottom: 14,
  },
  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#2A2622',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E5E0D6',
    borderRadius: 24,
    paddingHorizontal: 16,
    minHeight: 48,
    fontSize: 15,
    color: '#2A2622',
    backgroundColor: '#FFFFFF',
  },
  textarea: {
    minHeight: 88,
    borderRadius: 16,
    textAlignVertical: 'top',
    paddingTop: 12,
  },
  select: {
    borderWidth: 1,
    borderColor: '#E5E0D6',
    borderRadius: 24,
    paddingHorizontal: 16,
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
  },
  selectText: {
    fontSize: 15,
    color: '#2A2622',
  },
  placeholderText: {
    color: '#A8AEB4',
  },
  menu: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    marginTop: 6,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E8EDE4',
  },
  menuItem: {
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  menuText: {
    fontSize: 15,
    color: '#2A2622',
  },
  careIntro: {
    fontSize: 13,
    color: '#6F6A64',
    lineHeight: 20,
    marginBottom: 12,
  },
  radioRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 8,
  },
  radio: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: '#C5CBBE',
  },
  radioLabel: {
    fontSize: 15,
  },
  review: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  reviewHead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  reviewName: {
    fontSize: 18,
    fontWeight: '700',
  },
  reviewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    paddingVertical: 6,
  },
  reviewLabel: {
    fontSize: 13,
    color: '#6F6A64',
  },
  reviewValue: {
    fontSize: 13,
    fontWeight: '600',
    color: '#2A2622',
    textAlign: 'right',
    flex: 1,
  },
  confirmRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 10,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  confirmText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },
  verify: {
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 8,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 18,
  },
  backBtn: {
    height: 44,
    paddingHorizontal: 18,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: '#E5E0D6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  backText: {
    fontSize: 14,
    fontWeight: '600',
  },
  nextBtn: {
    height: 44,
    paddingHorizontal: 18,
    borderRadius: 22,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
});
