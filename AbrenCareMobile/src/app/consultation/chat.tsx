// consultation/chat.tsx

import React, { useEffect, useRef, useState } from "react";
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  ActivityIndicator,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import * as DocumentPicker from "expo-document-picker";
import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";

import { useConsultations } from "@/consultation/ConsultationContext";
import { doctorById, specialtyLabel } from "@/consultation/doctors";
import { useLanguage } from "@/i18n/LanguageContext";
import { useChat } from "@/contexts/ChatContext";
import { chatApi } from "@/services/chatApi";

const BLUE = "#6F89B9";

type FileKind = "photo" | "document" | "lab";

const fileIcons: Record<FileKind, keyof typeof Ionicons.glyphMap> = {
  photo: "image-outline",
  document: "document-text-outline",
  lab: "flask-outline",
};

function formatTime(iso: string) {
  const date = new Date(iso);
  const minutes = `${date.getMinutes()}`.padStart(2, "0");
  const suffix = date.getHours() >= 12 ? "PM" : "AM";
  const hour = date.getHours() % 12 === 0 ? 12 : date.getHours() % 12;
  return `${hour}:${minutes} ${suffix}`;
}

function inferKind(name?: string | null): FileKind {
  if (name && /\.(jpe?g|png|gif|webp)$/i.test(name)) return "photo";
  return "document";
}

export default function ConsultationChat() {
  const { t } = useLanguage();
  const router = useRouter();
  const params = useLocalSearchParams();
  const { draft, consultation, fetchConsultaion } = useConsultations();
  const scrollRef = useRef<ScrollView>(null);

  const {
    messages,
    loading,
    connected,
    typing,
    currentUserId,
    conversation,
    startConversationWith,
    sendMessage,
  } = useChat();

  const doctorId = params.doctor
  ? Number(params.doctor)
  : null;

  const [text, setText] = useState("");
  const [sheetOpen, setSheetOpen] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Kick off (or reuse) the private conversation once we know the doctor's id
  useEffect(() => {
    if (doctorId) {
      startConversationWith(Number(doctorId));
    }
  }, [doctorId]);

  useEffect(() => {
    fetchConsultaion(params.consultation);
  },[]);

  console.log(doctorId, 'doctor id', consultation, 'consultation id');
  console.log("params.doctor:", params.doctor);

  function handleSend() {
    const value = text.trim();
    if (!value) return;

    sendMessage(value);
    setText("");
  }

  console.log(messages, 'messages sent')

  async function pickAndSendPhoto() {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });

    if (result.canceled || !conversation) return;

    const asset = result.assets[0];
    await uploadAndClose({
      uri: asset.uri,
      name: asset.fileName ?? "photo.jpg",
      type: asset.mimeType ?? "image/jpeg",
    });
  }

  async function pickAndSendDocument() {
    const result = await DocumentPicker.getDocumentAsync({
      type: ["application/pdf", "image/*"],
      copyToCacheDirectory: true,
    });

    if (result.canceled || !conversation) return;

    const asset = result.assets[0];
    await uploadAndClose({
      uri: asset.uri,
      name: asset.name,
      type: asset.mimeType ?? "application/octet-stream",
    });
  }

  async function uploadAndClose(file: { uri: string; name: string; type: string }) {
    if (!conversation) return;

    setSheetOpen(false);
    setUploading(true);

    try {
      // The upload view broadcasts the new message over the socket,
      // so ChatContext's handleIncoming picks it up for every
      // connected participant, including this one — no manual append needed.
      await chatApi.uploadFile(conversation.id, file);
    } catch (err) {
      console.error("Upload failed:", err);
      // TODO: surface a toast/alert here
    } finally {
      setUploading(false);
    }
  }

  function handleAttachmentPress(kind: FileKind) {
    if (kind === "photo") {
      pickAndSendPhoto();
    } else {
      // "document" and "lab" both go through the file picker
      pickAndSendDocument();
    }
  }

  const attachments: { kind: FileKind; label: string }[] = [
    { kind: "photo", label: t.consultationChat.attachPhoto },
    { kind: "document", label: t.consultationChat.attachDocument },
    { kind: "lab", label: t.consultationChat.attachLab },
  ];

  const initials = consultation?.doctor_name.charAt(0) ?? "AC";

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} hitSlop={10}>
          <Ionicons name="chevron-back" size={22} color="#41597C" />
        </TouchableOpacity>

        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{initials}</Text>
        </View>

        <View style={styles.headerInfo}>
          <Text style={styles.name} numberOfLines={1}>
            {consultation?.doctor_name}
          </Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            {doctorId ? consultation?.specialty_name : ""}
          </Text>
        </View>

        <View style={styles.presence}>
          <View
            style={[
              styles.presenceDot,
              { backgroundColor: connected ? "#5A9964" : "#C9CDD2" },
            ]}
          />
          <Text
            style={[
              styles.presenceText,
              { color: connected ? "#4E8A58" : "#8D9297" },
            ]}
          >
            {connected
              ? t.consultationChat.online
              : t.consultationChat.offline}
          </Text>
        </View>

        <TouchableOpacity
          style={styles.callButton}
          onPress={() =>
            router.push({
              pathname: "/consultation/call",
              params: doctorId ? { doctor: doctorId } : undefined,
            })
          }
          accessibilityLabel={t.consultationChat.videoCall}
        >
          <Ionicons name="videocam" size={18} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {typing && (
        <View style={styles.noticeBar}>
          <Ionicons name="chatbubble-ellipses-outline" size={14} color="#8D9297" />
          <Text style={styles.noticeText}>
            {typing.username} {t.consultationChat.replyTime}
          </Text>
        </View>
      )}

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator color={BLUE} />
        </View>
      ) : (
        <ScrollView
          ref={scrollRef}
          style={styles.chatArea}
          contentContainerStyle={{ paddingBottom: 20 }}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={() =>
            scrollRef.current?.scrollToEnd({ animated: true })
          }
        >
          {messages.map((message) => {
            const isMine = message.sender_id === currentUserId;
            const hasFile = message.message_type !== "text" && message.file_url;

            return isMine ? (
              <View key={message.id} style={styles.myRow}>
                <View style={[styles.myBubble, hasFile && styles.fileBubble]}>
                  {hasFile ? (
                    <FileCard
                      name={message.file_name ?? "Attachment"}
                      url={message.file_url!}
                      openLabel={t.consultationChat.open}
                      outgoing
                    />
                  ) : (
                    <Text style={styles.myText}>{message.content}</Text>
                  )}
                </View>
                <Text style={styles.timeRight}>{formatTime(message.created_at)}</Text>
              </View>
            ) : (
              <View key={message.id} style={styles.theirRow}>
                <View style={styles.smallAvatar}>
                  <Text style={styles.smallAvatarText}>{initials}</Text>
                </View>

                <View>
                  <View style={styles.theirBubble}>
                    {hasFile ? (
                      <FileCard
                        name={message.file_name ?? "Attachment"}
                        url={message.file_url!}
                        openLabel={t.consultationChat.open}
                      />
                    ) : (
                      <Text style={styles.theirText}>{message.content}</Text>
                    )}
                  </View>
                  <Text style={styles.timeLeft}>{formatTime(message.created_at)}</Text>
                </View>
              </View>
            );
          })}
        </ScrollView>
      )}

      <View style={styles.inputBar}>
        <TouchableOpacity
          style={styles.attachButton}
          onPress={() => setSheetOpen(true)}
          accessibilityLabel={t.consultationChat.attachTitle}
          disabled={uploading}
        >
          {uploading ? (
            <ActivityIndicator size="small" color={BLUE} />
          ) : (
            <Ionicons name="attach" size={20} color={BLUE} />
          )}
        </TouchableOpacity>

        <TextInput
          value={text}
          onChangeText={setText}
          onSubmitEditing={handleSend}
          returnKeyType="send"
          placeholder={t.consultationChat.placeholder}
          placeholderTextColor="#A8AEB4"
          style={styles.input}
        />

        <TouchableOpacity style={styles.sendButton} onPress={handleSend}>
          <Ionicons name="send" size={18} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <Modal
        visible={sheetOpen}
        transparent
        animationType="slide"
        onRequestClose={() => setSheetOpen(false)}
      >
        <Pressable style={styles.backdrop} onPress={() => setSheetOpen(false)}>
          <Pressable style={styles.sheet}>
            <View style={styles.sheetHandle} />

            <Text style={styles.sheetTitle}>{t.consultationChat.attachTitle}</Text>
            <Text style={styles.sheetSubtitle}>{t.consultationChat.attachSubtitle}</Text>

            {attachments.map((attachment) => (
              <TouchableOpacity
                key={attachment.kind}
                style={styles.sheetRow}
                onPress={() => handleAttachmentPress(attachment.kind)}
              >
                <View style={styles.sheetIcon}>
                  <Ionicons name={fileIcons[attachment.kind]} size={18} color={BLUE} />
                </View>

                <View style={styles.sheetRowInfo}>
                  <Text style={styles.sheetRowLabel}>{attachment.label}</Text>
                </View>

                <Ionicons name="chevron-forward" size={16} color="#C7CCD2" />
              </TouchableOpacity>
            ))}

            <TouchableOpacity style={styles.sheetCancel} onPress={() => setSheetOpen(false)}>
              <Text style={styles.sheetCancelText}>{t.consultationChat.attachCancel}</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </Modal>
    </KeyboardAvoidingView>
  );
}

function FileCard({
  name,
  url,
  openLabel,
  outgoing,
}: {
  name: string;
  url: string;
  openLabel: string;
  outgoing?: boolean;
}) {
  const kind = inferKind(name);

  return (
    <TouchableOpacity
      style={styles.fileRow}
      onPress={() => {
        // Open in-browser / native viewer. Swap for Linking.openURL(url)
        // or a proper in-app viewer as needed.
      }}
    >
      <View style={[styles.fileIcon, outgoing && styles.fileIconOutgoing]}>
        <Ionicons name={fileIcons[kind]} size={18} color={outgoing ? "#FFFFFF" : BLUE} />
      </View>

      <View style={styles.fileInfo}>
        <Text
          style={[styles.fileName, outgoing && styles.fileTextOutgoing]}
          numberOfLines={1}
        >
          {name}
        </Text>
        <Text style={[styles.fileMeta, outgoing && styles.fileMetaOutgoing]}>
          {openLabel}
        </Text>
      </View>

      <Ionicons
        name="download-outline"
        size={16}
        color={outgoing ? "#DEE7F3" : "#9AA3AF"}
      />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#FAF9F6" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 15,
    paddingTop: 55,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#F1EFEB",
    backgroundColor: "#FFFFFF",
  },
  avatar: {
    width: 34, height: 34, borderRadius: 10,
    backgroundColor: "#EAF0F7", alignItems: "center", justifyContent: "center",
  },
  avatarText: { color: BLUE, fontWeight: "700", fontSize: 12 },
  headerInfo: { flex: 1 },
  name: { fontSize: 15, fontWeight: "700", color: "#172B42" },
  subtitle: { fontSize: 11, color: "#8D9297", marginTop: 2 },
  presence: { flexDirection: "row", alignItems: "center", gap: 5 },
  presenceDot: { width: 7, height: 7, borderRadius: 4 },
  presenceText: { fontSize: 11, fontWeight: "600" },
  callButton: {
    width: 36, height: 36, borderRadius: 12,
    backgroundColor: BLUE, alignItems: "center", justifyContent: "center",
  },
  noticeBar: {
    flexDirection: "row", alignItems: "center", gap: 7,
    paddingHorizontal: 18, paddingVertical: 10, backgroundColor: "#F4F7FB",
  },
  noticeText: { flex: 1, fontSize: 11, color: "#8D9297" },
  loadingContainer: { flex: 1, alignItems: "center", justifyContent: "center" },
  chatArea: { flex: 1, paddingHorizontal: 15, paddingTop: 15 },
  theirRow: { flexDirection: "row", marginBottom: 18 },
  smallAvatar: {
    width: 24, height: 24, borderRadius: 8, backgroundColor: "#EAF0F7",
    alignItems: "center", justifyContent: "center", marginRight: 8, marginTop: 4,
  },
  smallAvatarText: { color: BLUE, fontSize: 9, fontWeight: "700" },
  theirBubble: { backgroundColor: "#FFFFFF", borderRadius: 14, padding: 12, maxWidth: 270 },
  theirText: { color: "#374151", fontSize: 13, lineHeight: 19 },
  myRow: { alignItems: "flex-end", marginBottom: 18 },
  myBubble: { backgroundColor: BLUE, padding: 12, borderRadius: 14, maxWidth: 262 },
  fileBubble: { minWidth: 232 },
  myText: { color: "#FFFFFF", fontSize: 13, lineHeight: 19 },
  timeLeft: { fontSize: 10, color: "#AAA", marginTop: 4, marginLeft: 5 },
  timeRight: { fontSize: 10, color: "#AAA", marginTop: 4, marginRight: 5 },
  fileRow: { flexDirection: "row", alignItems: "center" },
  fileIcon: {
    width: 34, height: 34, borderRadius: 10, backgroundColor: "#EAF0F7",
    alignItems: "center", justifyContent: "center", marginRight: 10,
  },
  fileIconOutgoing: { backgroundColor: "rgba(255, 255, 255, 0.22)" },
  fileInfo: { flex: 1, marginRight: 8 },
  fileName: { fontSize: 13, fontWeight: "700", color: "#374151" },
  fileMeta: { fontSize: 11, color: "#9AA3AF", marginTop: 2 },
  fileTextOutgoing: { color: "#FFFFFF" },
  fileMetaOutgoing: { color: "#DEE7F3" },
  inputBar: {
    flexDirection: "row", alignItems: "center", gap: 10, padding: 12,
    borderTopWidth: 1, borderTopColor: "#F1EFEB", backgroundColor: "#FFFFFF",
  },
  attachButton: {
    width: 45, height: 45, borderRadius: 13, backgroundColor: "#EAF0F7",
    alignItems: "center", justifyContent: "center",
  },
  input: {
    flex: 1, backgroundColor: "#FFFFFF", borderWidth: 1, borderColor: "#E4E2DD",
    borderRadius: 13, paddingHorizontal: 14, height: 45, fontSize: 14, color: "#172B42",
  },
  sendButton: {
    width: 45, height: 45, borderRadius: 13, backgroundColor: BLUE,
    alignItems: "center", justifyContent: "center",
  },
  backdrop: { flex: 1, backgroundColor: "rgba(20, 24, 30, 0.45)", justifyContent: "flex-end" },
  sheet: {
    backgroundColor: "#FFFFFF", borderTopLeftRadius: 22, borderTopRightRadius: 22,
    paddingHorizontal: 18, paddingTop: 10, paddingBottom: 30,
  },
  sheetHandle: {
    alignSelf: "center", width: 40, height: 4, borderRadius: 2,
    backgroundColor: "#E3E3E3", marginBottom: 16,
  },
  sheetTitle: { fontSize: 17, fontWeight: "700", color: "#172B42" },
  sheetSubtitle: { fontSize: 12, color: "#9AA3AF", marginTop: 4, marginBottom: 14, lineHeight: 17 },
  sheetRow: {
    flexDirection: "row", alignItems: "center", paddingVertical: 12,
    borderTopWidth: 1, borderTopColor: "#F2F2F2",
  },
  sheetIcon: {
    width: 38, height: 38, borderRadius: 12, backgroundColor: "#EAF0F7",
    alignItems: "center", justifyContent: "center", marginRight: 12,
  },
  sheetRowInfo: { flex: 1 },
  sheetRowLabel: { fontSize: 14, fontWeight: "600", color: "#172B42" },
  sheetCancel: {
    marginTop: 16, height: 50, borderRadius: 14, backgroundColor: "#F4F7FB",
    alignItems: "center", justifyContent: "center",
  },
  sheetCancelText: { fontSize: 15, fontWeight: "600", color: BLUE },
});