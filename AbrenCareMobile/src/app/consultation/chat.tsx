import React, { useRef, useState } from "react";
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
} from "react-native";

import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";

import { useConsultations } from "@/consultation/ConsultationContext";
import { doctorById, specialtyLabel } from "@/consultation/doctors";
import { useLanguage } from "@/i18n/LanguageContext";

const BLUE = "#6F89B9";

type FileKind = "photo" | "document" | "lab";

type ChatMessage = {
  id: string;
  from: "me" | "them";
  time: string;
  text?: string;
  file?: { name: string; size: string; kind: FileKind };
};

const fileIcons: Record<FileKind, keyof typeof Ionicons.glyphMap> = {
  photo: "image-outline",
  document: "document-text-outline",
  lab: "flask-outline",
};

function nowTime() {
  const date = new Date();
  const minutes = `${date.getMinutes()}`.padStart(2, "0");
  const suffix = date.getHours() >= 12 ? "PM" : "AM";
  const hour = date.getHours() % 12 === 0 ? 12 : date.getHours() % 12;
  return `${hour}:${minutes} ${suffix}`;
}

export default function ConsultationChat() {
  const { t } = useLanguage();
  const router = useRouter();
  const params = useLocalSearchParams() as { doctor?: string };
  const { draft } = useConsultations();
  const scrollRef = useRef<ScrollView>(null);

  const doctor = doctorById(params.doctor ?? draft.doctorId);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "m1",
      from: "them",
      time: "10:52 AM",
      text: t.consultationChat.message1,
    },
    {
      id: "m2",
      from: "me",
      time: "11:04 AM",
      text: t.consultationChat.message2,
    },
    {
      id: "m3",
      from: "them",
      time: "11:06 AM",
      text: t.consultationChat.message3,
    },
  ]);
  const [text, setText] = useState("");
  const [sheetOpen, setSheetOpen] = useState(false);

  function append(message: Omit<ChatMessage, "id" | "time">) {
    setMessages((current) => [
      ...current,
      { ...message, id: `m-${Date.now()}-${current.length}`, time: nowTime() },
    ]);
  }

  function handleSend() {
    const value = text.trim();
    if (!value) {
      return;
    }

    append({ from: "me", text: value });
    setText("");
  }

  function shareFile(kind: FileKind, name: string, size: string) {
    setSheetOpen(false);
    append({ from: "me", file: { name, size, kind } });

    setTimeout(() => {
      append({ from: "them", text: t.consultationChat.fileReply });
    }, 1200);
  }

  const attachments: {
    kind: FileKind;
    label: string;
    name: string;
    size: string;
  }[] = [
    {
      kind: "photo",
      label: t.consultationChat.attachPhoto,
      name: "symptom-photo.jpg",
      size: "1.2 MB",
    },
    {
      kind: "document",
      label: t.consultationChat.attachDocument,
      name: "referral-letter.pdf",
      size: "240 KB",
    },
    {
      kind: "lab",
      label: t.consultationChat.attachLab,
      name: "blood-panel.pdf",
      size: "186 KB",
    },
  ];

  const initials = doctor?.initials ?? "AC";

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
            {doctor?.name}
          </Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            {doctor ? specialtyLabel(doctor.specialty, t) : ""}
          </Text>
        </View>

        <View style={styles.presence}>
          <View
            style={[
              styles.presenceDot,
              { backgroundColor: doctor?.online ? "#5A9964" : "#C9CDD2" },
            ]}
          />
          <Text
            style={[
              styles.presenceText,
              { color: doctor?.online ? "#4E8A58" : "#8D9297" },
            ]}
          >
            {doctor?.online
              ? t.consultationChat.online
              : t.consultationChat.offline}
          </Text>
        </View>

        <TouchableOpacity
          style={styles.callButton}
          onPress={() =>
            router.push({
              pathname: "/consultation/call",
              params: doctor ? { doctor: doctor.id } : undefined,
            })
          }
          accessibilityLabel={t.consultationChat.videoCall}
        >
          <Ionicons name="videocam" size={18} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <View style={styles.noticeBar}>
        <Ionicons
          name={doctor?.online ? "chatbubble-ellipses-outline" : "time-outline"}
          size={14}
          color="#8D9297"
        />
        <Text style={styles.noticeText}>
          {doctor?.online
            ? t.consultationChat.replyTime
            : t.consultationChat.awayNotice}
        </Text>
      </View>

      <ScrollView
        ref={scrollRef}
        style={styles.chatArea}
        contentContainerStyle={{ paddingBottom: 20 }}
        showsVerticalScrollIndicator={false}
        onContentSizeChange={() =>
          scrollRef.current?.scrollToEnd({ animated: true })
        }
      >
        {messages.map((message) =>
          message.from === "them" ? (
            <View key={message.id} style={styles.theirRow}>
              <View style={styles.smallAvatar}>
                <Text style={styles.smallAvatarText}>{initials}</Text>
              </View>

              <View>
                <View style={styles.theirBubble}>
                  {message.file ? (
                    <FileCard
                      file={message.file}
                      openLabel={t.consultationChat.open}
                    />
                  ) : (
                    <Text style={styles.theirText}>{message.text}</Text>
                  )}
                </View>

                <Text style={styles.timeLeft}>{message.time}</Text>
              </View>
            </View>
          ) : (
            <View key={message.id} style={styles.myRow}>
              <View
                style={[styles.myBubble, message.file && styles.fileBubble]}
              >
                {message.file ? (
                  <FileCard
                    file={message.file}
                    openLabel={t.consultationChat.open}
                    outgoing
                  />
                ) : (
                  <Text style={styles.myText}>{message.text}</Text>
                )}
              </View>

              <Text style={styles.timeRight}>{message.time}</Text>
            </View>
          ),
        )}
      </ScrollView>

      <View style={styles.inputBar}>
        <TouchableOpacity
          style={styles.attachButton}
          onPress={() => setSheetOpen(true)}
          accessibilityLabel={t.consultationChat.attachTitle}
        >
          <Ionicons name="attach" size={20} color={BLUE} />
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

            <Text style={styles.sheetTitle}>
              {t.consultationChat.attachTitle}
            </Text>
            <Text style={styles.sheetSubtitle}>
              {t.consultationChat.attachSubtitle}
            </Text>

            {attachments.map((attachment) => (
              <TouchableOpacity
                key={attachment.kind}
                style={styles.sheetRow}
                onPress={() =>
                  shareFile(attachment.kind, attachment.name, attachment.size)
                }
              >
                <View style={styles.sheetIcon}>
                  <Ionicons
                    name={fileIcons[attachment.kind]}
                    size={18}
                    color={BLUE}
                  />
                </View>

                <View style={styles.sheetRowInfo}>
                  <Text style={styles.sheetRowLabel}>{attachment.label}</Text>
                  <Text style={styles.sheetRowMeta}>
                    {attachment.name} · {attachment.size}
                  </Text>
                </View>

                <Ionicons name="chevron-forward" size={16} color="#C7CCD2" />
              </TouchableOpacity>
            ))}

            <TouchableOpacity
              style={styles.sheetCancel}
              onPress={() => setSheetOpen(false)}
            >
              <Text style={styles.sheetCancelText}>
                {t.consultationChat.attachCancel}
              </Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </Modal>
    </KeyboardAvoidingView>
  );
}

function FileCard({
  file,
  openLabel,
  outgoing,
}: {
  file: { name: string; size: string; kind: FileKind };
  openLabel: string;
  outgoing?: boolean;
}) {
  return (
    <View style={styles.fileRow}>
      <View style={[styles.fileIcon, outgoing && styles.fileIconOutgoing]}>
        <Ionicons
          name={fileIcons[file.kind]}
          size={18}
          color={outgoing ? "#FFFFFF" : BLUE}
        />
      </View>

      <View style={styles.fileInfo}>
        <Text
          style={[styles.fileName, outgoing && styles.fileTextOutgoing]}
          numberOfLines={1}
        >
          {file.name}
        </Text>
        <Text style={[styles.fileMeta, outgoing && styles.fileMetaOutgoing]}>
          {file.size} · {openLabel}
        </Text>
      </View>

      <Ionicons
        name="download-outline"
        size={16}
        color={outgoing ? "#DEE7F3" : "#9AA3AF"}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FAF9F6",
  },

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
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
  },

  avatarText: {
    color: BLUE,
    fontWeight: "700",
    fontSize: 12,
  },

  headerInfo: {
    flex: 1,
  },

  name: {
    fontSize: 15,
    fontWeight: "700",
    color: "#172B42",
  },

  subtitle: {
    fontSize: 11,
    color: "#8D9297",
    marginTop: 2,
  },

  presence: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },

  presenceDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },

  presenceText: {
    fontSize: 11,
    fontWeight: "600",
  },

  callButton: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: BLUE,
    alignItems: "center",
    justifyContent: "center",
  },

  noticeBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    paddingHorizontal: 18,
    paddingVertical: 10,
    backgroundColor: "#F4F7FB",
  },

  noticeText: {
    flex: 1,
    fontSize: 11,
    color: "#8D9297",
  },

  chatArea: {
    flex: 1,
    paddingHorizontal: 15,
    paddingTop: 15,
  },

  theirRow: {
    flexDirection: "row",
    marginBottom: 18,
  },

  smallAvatar: {
    width: 24,
    height: 24,
    borderRadius: 8,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 8,
    marginTop: 4,
  },

  smallAvatarText: {
    color: BLUE,
    fontSize: 9,
    fontWeight: "700",
  },

  theirBubble: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 12,
    maxWidth: 270,
  },

  theirText: {
    color: "#374151",
    fontSize: 13,
    lineHeight: 19,
  },

  myRow: {
    alignItems: "flex-end",
    marginBottom: 18,
  },

  myBubble: {
    backgroundColor: BLUE,
    padding: 12,
    borderRadius: 14,
    maxWidth: 262,
  },

  fileBubble: {
    minWidth: 232,
  },

  myText: {
    color: "#FFFFFF",
    fontSize: 13,
    lineHeight: 19,
  },

  timeLeft: {
    fontSize: 10,
    color: "#AAA",
    marginTop: 4,
    marginLeft: 5,
  },

  timeRight: {
    fontSize: 10,
    color: "#AAA",
    marginTop: 4,
    marginRight: 5,
  },

  fileRow: {
    flexDirection: "row",
    alignItems: "center",
  },

  fileIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 10,
  },

  fileIconOutgoing: {
    backgroundColor: "rgba(255, 255, 255, 0.22)",
  },

  fileInfo: {
    flex: 1,
    marginRight: 8,
  },

  fileName: {
    fontSize: 13,
    fontWeight: "700",
    color: "#374151",
  },

  fileMeta: {
    fontSize: 11,
    color: "#9AA3AF",
    marginTop: 2,
  },

  fileTextOutgoing: {
    color: "#FFFFFF",
  },

  fileMetaOutgoing: {
    color: "#DEE7F3",
  },

  inputBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: "#F1EFEB",
    backgroundColor: "#FFFFFF",
  },

  attachButton: {
    width: 45,
    height: 45,
    borderRadius: 13,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
  },

  input: {
    flex: 1,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E4E2DD",
    borderRadius: 13,
    paddingHorizontal: 14,
    height: 45,
    fontSize: 14,
    color: "#172B42",
  },

  sendButton: {
    width: 45,
    height: 45,
    borderRadius: 13,
    backgroundColor: BLUE,
    alignItems: "center",
    justifyContent: "center",
  },

  backdrop: {
    flex: 1,
    backgroundColor: "rgba(20, 24, 30, 0.45)",
    justifyContent: "flex-end",
  },

  sheet: {
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    paddingHorizontal: 18,
    paddingTop: 10,
    paddingBottom: 30,
  },

  sheetHandle: {
    alignSelf: "center",
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: "#E3E3E3",
    marginBottom: 16,
  },

  sheetTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: "#172B42",
  },

  sheetSubtitle: {
    fontSize: 12,
    color: "#9AA3AF",
    marginTop: 4,
    marginBottom: 14,
    lineHeight: 17,
  },

  sheetRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: "#F2F2F2",
  },

  sheetIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },

  sheetRowInfo: {
    flex: 1,
  },

  sheetRowLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#172B42",
  },

  sheetRowMeta: {
    fontSize: 11,
    color: "#9AA3AF",
    marginTop: 2,
  },

  sheetCancel: {
    marginTop: 16,
    height: 50,
    borderRadius: 14,
    backgroundColor: "#F4F7FB",
    alignItems: "center",
    justifyContent: "center",
  },

  sheetCancelText: {
    fontSize: 15,
    fontWeight: "600",
    color: BLUE,
  },
});
