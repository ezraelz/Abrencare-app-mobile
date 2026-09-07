import { api } from '@/services/api';
import { familyMember, familyPatient, familyService } from '@/types/familyTypes';
import React, { useState } from 'react'

export const useFamilyService = () => {
    const [ familyServices, setFamilyServices ] = useState<familyService[]>([]);
    const [ familyService, setFamilyService ] = useState<familyService>();
    const [ familyMembers, setFamilyMembers ] = useState<familyMember[]>([]);
    const [ familyPatients, setFamilyPatients ] = useState<familyPatient[]>([]);
    const [ isLoading, setIsLoading ] = useState(false);
    const [ error, setError ] = useState("");

    const fetchFamilyServices = async () => {
        setIsLoading(true);
        setError("");
        try{
            const res = await api.get('/api/families/');
            setFamilyServices(res.data);
        }catch(error){
            setError(`Faild to fetch family services. ${error}`);
            setIsLoading(false);
        }finally{
            setIsLoading(false);
        }
    }

    const fetchFamilyService = async (id: number)=> {
        setIsLoading(true);
        setError("");
        try{
            const res = await api.get(`/api/families/${id}/`);
            setFamilyService(res.data);
        }catch(errors){
            setError(`Faild to fetch family service. ${errors}`)
        }finally{
            setIsLoading(false);
        }
    }

    const fetchFamilyMembers = async (id: number) => {
        setIsLoading(true);
        setError("");
        try{
            const res = await api.get(`/api/families/${id}/members/`);
            setFamilyMembers(res.data);
        }catch(errors){
            setError(`Faild to fetch family members.${errors}`);
            setIsLoading(false);
        }finally{
            setIsLoading(false);
        }
    }

    const fetchFamilyPatients = async (id: number) => {
        setIsLoading(true);
        setError("");
        try{
            const res = await api.get(`/api/families/${id}/patents/`);
            setFamilyPatients(res.data);
        }catch(errors){
            setError(`Faild to fetch family patients.${errors}`);
            setIsLoading(false);
        }finally{
            setIsLoading(false);
        }
    }

  return {
    error,
    isLoading,

    familyService,
    familyServices,
    familyMembers,
    familyPatients,

    fetchFamilyMembers,
    fetchFamilyPatients,
    fetchFamilyService,
    fetchFamilyServices,
  }
}
