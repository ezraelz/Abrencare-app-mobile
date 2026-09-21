import { StyleSheet, View } from 'react-native';

import { Ionicons } from '@expo/vector-icons';

type Props = {
  color: string;
};

export default function MedicalDecor({ color }: Props) {
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <View style={[styles.ring, styles.ringLarge, { borderColor: color }]} />
      <View style={[styles.ring, styles.ringMid, { borderColor: color }]} />

      <View style={[styles.cross, styles.crossTopRight]}>
        <View style={[styles.crossBar, styles.crossV, { backgroundColor: color }]} />
        <View style={[styles.crossBar, styles.crossH, { backgroundColor: color }]} />
      </View>

      <View style={[styles.cross, styles.crossBottomLeft]}>
        <View style={[styles.crossBar, styles.crossVSmall, { backgroundColor: color }]} />
        <View style={[styles.crossBar, styles.crossHSmall, { backgroundColor: color }]} />
      </View>

      <Ionicons
        name="pulse-outline"
        size={88}
        color={color}
        style={styles.pulseIcon}
      />
      <Ionicons
        name="medkit-outline"
        size={54}
        color={color}
        style={styles.kitIcon}
      />

      <View style={styles.ecg}>
        {ECG_SEGMENTS.map((segment, index) => (
          <View
            key={index}
            style={[
              styles.ecgSeg,
              {
                width: segment.width,
                height: segment.height,
                marginBottom: segment.lift,
                backgroundColor: color,
              },
            ]}
          />
        ))}
      </View>
    </View>
  );
}

const ECG_SEGMENTS = [
  { width: 28, height: 2, lift: 0 },
  { width: 10, height: 2, lift: 10 },
  { width: 8, height: 2, lift: -18 },
  { width: 8, height: 2, lift: 22 },
  { width: 10, height: 2, lift: 0 },
  { width: 36, height: 2, lift: 0 },
  { width: 10, height: 2, lift: 8 },
  { width: 8, height: 2, lift: -16 },
  { width: 8, height: 2, lift: 18 },
  { width: 14, height: 2, lift: 0 },
  { width: 48, height: 2, lift: 0 },
];

const styles = StyleSheet.create({
  ring: {
    position: 'absolute',
    borderWidth: 1.5,
    borderRadius: 999,
    opacity: 0.1,
  },
  ringLarge: {
    width: 280,
    height: 280,
    top: -90,
    right: -90,
  },
  ringMid: {
    width: 180,
    height: 180,
    top: -40,
    right: -40,
  },
  cross: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.12,
  },
  crossTopRight: {
    top: 36,
    right: 18,
  },
  crossBottomLeft: {
    bottom: 210,
    left: 18,
  },
  crossBar: {
    position: 'absolute',
    borderRadius: 4,
  },
  crossV: {
    width: 18,
    height: 72,
  },
  crossH: {
    width: 72,
    height: 18,
  },
  crossVSmall: {
    width: 12,
    height: 44,
  },
  crossHSmall: {
    width: 44,
    height: 12,
  },
  pulseIcon: {
    position: 'absolute',
    bottom: 88,
    right: 16,
    opacity: 0.12,
  },
  kitIcon: {
    position: 'absolute',
    top: 120,
    left: 12,
    opacity: 0.1,
    transform: [{ rotate: '-12deg' }],
  },
  ecg: {
    position: 'absolute',
    left: 20,
    right: 20,
    bottom: 42,
    flexDirection: 'row',
    alignItems: 'flex-end',
    opacity: 0.16,
  },
  ecgSeg: {
    borderRadius: 1,
  },
});
