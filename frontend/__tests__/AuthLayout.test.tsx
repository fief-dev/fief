import { render, screen } from '@testing-library/react';

import AuthLayout from '../components/AuthLayout/AuthLayout';

describe('AuthLayout', () => {
  it('should show the provided title', async () => {
    render(<AuthLayout title="Title" tenantName="Tenant" />);

    expect(screen.queryByText('Title')).not.toBeNull();
  });

  it('should show the tenant name if logo not provided', async () => {
    render(<AuthLayout title="Title" tenantName="Tenant" />);

    expect(screen.queryByText('Tenant')).not.toBeNull();
    expect(screen.queryByAltText('Tenant')).toBeNull();
  });

  it('should show the tenant logo if provided', async () => {
    render(<AuthLayout title="Title" tenantName="Tenant" tenantLogoURL="/logo.png" />);

    expect(screen.queryByText('Tenant')).toBeNull();
    expect(screen.queryByAltText('Tenant')).not.toBeNull();
  });
});
