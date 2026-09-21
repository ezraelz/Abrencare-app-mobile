import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

type DoctorCardProps = {
  name: string;
  specialty: string;
  availability?: string;
  rating?: string;
};

export default function DoctorCard({ name, specialty, availability, rating }: DoctorCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.name}>{name}</Text>
      <Text style={styles.specialty}>{specialty}</Text>
      {availability ? <Text style={styles.availability}>{availability}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  name: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  specialty: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  availability: {
    fontSize: 12,
    color: '#7E93A8',
    marginTop: 8,
  },
});
