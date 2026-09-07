import { api } from '@/services/api';
import { Consultaions } from '@/types/consultationsTypes';
import React, { useState } from 'react'

export const useConsultations = () => {
    const [ consultations, setConsultations ] =  useState<Consultaions[]>([]);
    const [ consultation, setConsultation ] = useState<Consultaions>();
    const [ isLoading, setIsLoading ] = useState(false);
    const [ errors, setErrors ] = useState("");

    const fetchConsultaions = async ()=> {
        setIsLoading(true);
        setErrors("");
        try{
            const res = await api.get('/api/consultations/mine/');
            setConsultations(res.data);
        }catch(errors){
            setErrors(`Faild to fetch consultations. ${errors}`);
            setIsLoading(false)
        }finally{
            setIsLoading(false);
        }
    }

    const fetchConsultaion = async (id: number)=> {
        setIsLoading(true);
        setErrors("");
        try{
            const res = await api.get(`/api/consultations/${id}/`);
            setConsultation(res.data);
        }catch(errors){
            setErrors(`Faild to fetch consultations. ${errors}`);
            setIsLoading(false);
        }finally{
            setIsLoading(false);
        }
    }

    const createConsultations = async ()=> {
        setIsLoading(true);
        setErrors("");
        try{
            const res = await api.post('/api/consultations/');
        }catch(errors){
            setErrors(`Faild to create a consultations. ${errors}`);
            setIsLoading(false);
        }finally{
            setIsLoading(false);
        }
    }

    const cancelConsultation = async (id: number)=> {
        setIsLoading(true);
        setErrors("");
        try{
            const res = await api.post(`/api/consultations/${id}/`);
        }catch(error){
            setIsLoading(false);
            setErrors(`Faild to cancel consultations. ${error}`);
        }finally{
            setIsLoading(false);
        }
    }

  return {
    isLoading,
    errors,

    consultation,
    consultations,

    fetchConsultaion,
    fetchConsultaions,
    createConsultations,
    cancelConsultation,
  }
}
