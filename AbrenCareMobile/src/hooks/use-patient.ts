import { doctorsInSpecialty } from '@/consultation/doctors';
import { api } from '@/services/api';
import { Patients } from '@/types/patientTypes';
import React, { useState } from 'react'

export const usePatients = () => {
    const [ patients, setPatients ] = useState<Patients[]>([]);
    const [ patient, setPatient ] = useState<Patients>();
    const [ isLoading, setIsLoading ] = useState(false);
    const [ error, setError ] = useState("");

    const fetchPatients = async () => {
        setIsLoading(true);
        setError("");
        try{
            const res = await api.get('/api/patients/');
            setPatients(res.data);
        }catch(error){
            setError(`Faild to fetch patients. ${error}`);
            setIsLoading(false);
        }finally{
            setIsLoading(false);
        }
    }

    const fetchPatient = async (id: number)=> {
        setIsLoading(true);
        setError("");
        try{
            const res = await api.get(`/api/patients/${id}/`);
            setPatient(res.data);
        }catch(errors){
            setError(`Faild to fetch patient. ${errors}`)
        }finally{
            setIsLoading(false);
        }
    }

  return {
    error,
    isLoading,

    patient,
    patients,

    fetchPatient,
    fetchPatients
  }
}
