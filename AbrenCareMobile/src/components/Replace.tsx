import { useEffect } from 'react';

import { useRouter } from 'expo-router';

export default function Replace({ href }: { href: string }) {
  const router = useRouter();

  useEffect(() => {
    router.replace(href);
  }, [href, router]);

  return null;
}
