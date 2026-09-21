import React, { useRef, useState } from 'react';
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
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useLanguage } from '@/i18n/LanguageContext';

type FileKind = 'photo' | 'document' | 'lab';

type ChatMessage = {
  id: string;
  from: 'me' | 'them';
  time: string;
  text?: string;
  file?: { name: string; size: string; kind: FileKind };
};

const fileIcons: Record<FileKind, keyof typeof Ionicons.glyphMap> = {
  photo: 'image-outline',
  document: 'document-text-outline',
  lab: 'flask-outline',
};

function nowTime() {
  const date = new Date();
  const minutes = `${date.getMinutes()}`.padStart(2, '0');
  const suffix = date.getHours() >= 12 ? 'PM' : 'AM';
  const hour = date.getHours() % 12 === 0 ? 12 : date.getHours() % 12;
  return `${hour}:${minutes} ${suffix}`;
}

export default function FamilyChat() {
  const { t } = useLanguage();
  const router = useRouter();
  const scrollRef = useRef<ScrollView>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 'm1', from: 'them', time: '10:52 AM', text: t.familyChat.message1 },
    { id: 'm2', from: 'me', time: '11:04 AM', text: t.familyChat.message2 },
    { id: 'm3', from: 'them', time: '11:06 AM', text: t.familyChat.message3 },
  ]);
  const [draft, setDraft] = useState('');
  const [sheetOpen, setSheetOpen] = useState(false);

  function append(message: Omit<ChatMessage, 'id' | 'time'>) {
    setMessages((current) => [
      ...current,
      { ...message, id: `m-${Date.now()}-${current.length}`, time: nowTime() },
    ]);
  }

  function handleSend() {
    const text = draft.trim();
    if (!text) {
      return;
    }

    append({ from: 'me', text });
    setDraft('');
  }

  function shareFile(kind: FileKind, name: string, size: string) {
    setSheetOpen(false);
    append({ from: 'me', file: { name, size, kind } });

    setTimeout(() => {
      append({ from: 'them', text: t.familyChat.fileReply });
    }, 1200);
  }

  const attachments: {
    kind: FileKind;
    label: string;
    name: string;
    size: string;
  }[] = [
    {
      kind: 'photo',
      label: t.familyChat.attachPhoto,
      name: 'ankle-photo.jpg',
      size: '1.4 MB',
    },
    {
      kind: 'document',
      label: t.familyChat.attachDocument,
      name: 'discharge-summary.pdf',
      size: '320 KB',
    },
    {
      kind: 'lab',
      label: t.familyChat.attachLab,
      name: 'blood-panel-14-june.pdf',
      size: '186 KB',
    },
  ];

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} hitSlop={10}>
          <Ionicons name="chevron-back" size={22} color="#444" />
        </TouchableOpacity>

        <View style={styles.avatar}>
          <Text style={styles.avatarText}>MT</Text>
        </View>

        <View style={styles.headerInfo}>
          <Text style={styles.name}>Marta Tesfaye</Text>
          <Text style={styles.subtitle}>
            {t.familyChat.coordinatorSubtitle}
          </Text>
        </View>

        <View style={styles.onlineContainer}>
          <View style={styles.onlineDot} />
          <Text style={styles.online}>{t.familyChat.online}</Text>
        </View>

        <TouchableOpacity
          style={styles.callButton}
          onPress={() => router.push('/family/call')}
          accessibilityLabel={t.familyChat.videoCall}
        >
          <Ionicons name="videocam" size={18} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Messages */}
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
          message.from === 'them' ? (
            <View key={message.id} style={styles.messageRow}>
              <View style={styles.smallAvatar}>
                <Text style={styles.smallAvatarText}>MT</Text>
              </View>

              <View>
                <View style={styles.receiverBubble}>
                  {message.file ? (
                    <FileCard file={message.file} openLabel={t.familyChat.open} />
                  ) : (
                    <Text style={styles.receiverText}>{message.text}</Text>
                  )}
                </View>

                <Text style={styles.timeLeft}>{message.time}</Text>
              </View>
            </View>
          ) : (
            <View key={message.id} style={styles.myRow}>
              <View style={[styles.myBubble, message.file && styles.fileBubble]}>
                {message.file ? (
                  <FileCard
                    file={message.file}
                    openLabel={t.familyChat.open}
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

      {/* Message Box */}
      <View style={styles.inputContainer}>
        <TouchableOpacity
          style={styles.attachButton}
          onPress={() => setSheetOpen(true)}
          accessibilityLabel={t.familyChat.attachTitle}
        >
          <Ionicons name="attach" size={20} color="#8B9A7C" />
        </TouchableOpacity>

        <TextInput
          value={draft}
          onChangeText={setDraft}
          onSubmitEditing={handleSend}
          returnKeyType="send"
          placeholder={t.familyChat.placeholder}
          placeholderTextColor="#999"
          style={styles.input}
        />

        <TouchableOpacity style={styles.sendButton} onPress={handleSend}>
          <Ionicons name="send" color="white" size={18} />
        </TouchableOpacity>
      </View>

      {/* File sharing sheet */}
      <Modal
        visible={sheetOpen}
        transparent
        animationType="slide"
        onRequestClose={() => setSheetOpen(false)}
      >
        <Pressable style={styles.backdrop} onPress={() => setSheetOpen(false)}>
          <Pressable style={styles.sheet}>
            <View style={styles.sheetHandle} />

            <Text style={styles.sheetTitle}>{t.familyChat.attachTitle}</Text>
            <Text style={styles.sheetSubtitle}>
              {t.familyChat.attachSubtitle}
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
                    color="#8B9A7C"
                  />
                </View>

                <View style={styles.sheetRowInfo}>
                  <Text style={styles.sheetRowLabel}>{attachment.label}</Text>
                  <Text style={styles.sheetRowMeta}>
                    {attachment.name} · {attachment.size}
                  </Text>
                </View>

                <Ionicons name="chevron-forward" size={16} color="#C7CCC2" />
              </TouchableOpacity>
            ))}

            <TouchableOpacity
              style={styles.sheetCancel}
              onPress={() => setSheetOpen(false)}
            >
              <Text style={styles.sheetCancelText}>
                {t.familyChat.attachCancel}
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
          color={outgoing ? '#FFFFFF' : '#8B9A7C'}
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
        color={outgoing ? '#E7EFE3' : '#9AA3AF'}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F6F2EA',
  },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 15,
    paddingTop: 55,
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#EEE',
    backgroundColor: '#FFF',
  },

  avatar: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#1F2937',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 10,
  },

  avatarText: {
    color: '#B8F18D',
    fontWeight: '700',
    fontSize: 12,
  },

  headerInfo: {
    flex: 1,
    marginLeft: 10,
  },

  name: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1E293B',
  },

  subtitle: {
    fontSize: 11,
    color: '#999',
    marginTop: 2,
  },

  onlineContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  onlineDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#4CAF50',
    marginRight: 5,
  },

  online: {
    color: '#4CAF50',
    fontSize: 11,
  },

  callButton: {
    width: 34,
    height: 34,
    borderRadius: 11,
    backgroundColor: '#8B9A7C',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 10,
  },

  chatArea: {
    flex: 1,
    padding: 15,
  },

  messageRow: {
    flexDirection: 'row',
    marginBottom: 18,
  },

  smallAvatar: {
    width: 22,
    height: 22,
    borderRadius: 6,
    backgroundColor: '#1F2937',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
    marginTop: 4,
  },

  smallAvatarText: {
    color: '#B8F18D',
    fontSize: 8,
    fontWeight: '700',
  },

  receiverBubble: {
    backgroundColor: '#FFF',
    borderRadius: 14,
    padding: 12,
    maxWidth: 270,
    elevation: 1,
  },

  receiverText: {
    color: '#374151',
    fontSize: 13,
    lineHeight: 18,
  },

  myRow: {
    alignItems: 'flex-end',
    marginBottom: 18,
  },

  myBubble: {
    backgroundColor: '#8B9A7C',
    padding: 12,
    borderRadius: 14,
    maxWidth: 260,
  },

  fileBubble: {
    minWidth: 230,
  },

  myText: {
    color: '#FFF',
    fontSize: 13,
    lineHeight: 18,
  },

  timeLeft: {
    fontSize: 10,
    color: '#AAA',
    marginTop: 4,
    marginLeft: 5,
  },

  timeRight: {
    fontSize: 10,
    color: '#AAA',
    marginTop: 4,
    marginRight: 5,
  },

  fileRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  fileIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: '#E8EDE4',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  fileIconOutgoing: {
    backgroundColor: 'rgba(255,255,255,0.22)',
  },

  fileInfo: {
    flex: 1,
    marginRight: 8,
  },

  fileName: {
    fontSize: 13,
    fontWeight: '700',
    color: '#374151',
  },

  fileMeta: {
    fontSize: 11,
    color: '#9AA3AF',
    marginTop: 2,
  },

  fileTextOutgoing: {
    color: '#FFFFFF',
  },

  fileMetaOutgoing: {
    color: '#E7EFE3',
  },

  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: '#EEE',
    backgroundColor: '#FFF',
  },

  attachButton: {
    width: 45,
    height: 45,
    borderRadius: 12,
    backgroundColor: '#E8EDE4',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  input: {
    flex: 1,
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 12,
    paddingHorizontal: 14,
    height: 45,
    fontSize: 14,
  },

  sendButton: {
    width: 45,
    height: 45,
    borderRadius: 12,
    backgroundColor: '#8B9A7C',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 10,
  },

  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(17, 24, 20, 0.45)',
    justifyContent: 'flex-end',
  },

  sheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    paddingHorizontal: 18,
    paddingTop: 10,
    paddingBottom: 30,
  },

  sheetHandle: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#E3E3E3',
    marginBottom: 16,
  },

  sheetTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#2A2622',
  },

  sheetSubtitle: {
    fontSize: 12,
    color: '#9AA3AF',
    marginTop: 4,
    marginBottom: 14,
    lineHeight: 17,
  },

  sheetRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#F2F2F2',
  },

  sheetIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#E8EDE4',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  sheetRowInfo: {
    flex: 1,
  },

  sheetRowLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2A2622',
  },

  sheetRowMeta: {
    fontSize: 11,
    color: '#9AA3AF',
    marginTop: 2,
  },

  sheetCancel: {
    marginTop: 16,
    height: 50,
    borderRadius: 14,
    backgroundColor: '#E8EDE4',
    alignItems: 'center',
    justifyContent: 'center',
  },

  sheetCancelText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#5E7054',
  },
});
