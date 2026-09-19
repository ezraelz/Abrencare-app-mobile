import Replace from '@/components/Replace';

import { useAuth } from '@/auth/AuthContext';
import { dashboardFor, onboardingPath } from '@/auth/serviceTheme';
import type { CareService } from '@/auth/types';

type Props = {
  service: CareService;
  children: React.ReactNode;
};

export default function ServiceAccessGate({ service, children }: Props) {
  const { isSignedIn, hasService, needsOnboarding } = useAuth();

  if (!isSignedIn || !hasService(service)) {
    return (
      <Replace href={`/signup?service=${service}`} />
    );
  }

  if (needsOnboarding(service)) {
    return <Replace href={onboardingPath(service)} />;
  }

  return <>{children}</>;
}

export function serviceHome(service: CareService) {
  return dashboardFor(service);
}
