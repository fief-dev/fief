import { render, screen } from '@testing-library/react';

import * as schemas from '../../schemas';
import AuthLayout from './AuthLayout';

const tenant: schemas.tenant.TenantReadPublic = {
  id: 'aaa',
  name: 'Tenant',
  default: true,
  logo_url: null,
};

describe('AuthLayout', () => {
  it('should show the provided title', async () => {
    render(<AuthLayout title="Title" tenant={tenant} />);

    expect(screen.getByText('Title')).toBeDefined()
  });

  it('should show the tenant name if logo not provided', async () => {
    render(<AuthLayout title="Title" tenant={tenant} />);

    expect(screen.getByText('Tenant')).toBeDefined();
    expect(screen.queryByAltText('Tenant')).toBeNull();
  });

  it('should show the tenant logo if provided', async () => {
    render(<AuthLayout title="Title" tenant={{ ...tenant, logo_url: '/logo.png' }} />);

    expect(screen.queryByText('Tenant')).toBeNull();
    expect(screen.getByAltText('Tenant')).toBeDefined();
  });
});
