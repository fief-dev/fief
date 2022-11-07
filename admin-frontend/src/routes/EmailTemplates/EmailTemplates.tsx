import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Column } from 'react-table';

import DataTable from '../../components/DataTable/DataTable';
import Layout from '../../components/Layout/Layout';
import { usePaginationAPI } from '../../hooks/api';
import * as schemas from '../../schemas';

const EmailTemplates: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const { t } = useTranslation(['email-templates']);
  const {
    data: emailTemplates,
    count,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
  } = usePaginationAPI<'listEmailTemplates'>({ method: 'listEmailTemplates', limit: 10 });

  const columns = useMemo<Column<schemas.emailTemplate.EmailTemplate>[]>(() => {
    return [
      {
        Header: t('list.type') as string,
        accessor: 'type',
        Cell: ({ cell: { value } }) => (
          <span className="font-medium text-slate-800 hover:text-slate-900 cursor-pointer">{t(`email_template_type.${value}`)}</span>
        ),
      },
      {
        Header: t('list.subject') as string,
        accessor: 'subject',
      },
      {
        id: 'actions',
        disableSortBy: true,
        accessor: 'id',
        Header: t('list.actions') as string,
        Cell: ({ row: { original } }) => (
          <div className="flex justify-end">
            <Link
              to={`/email-templates/${original.id}`}
              className="btn-xs bg-primary-500 hover:bg-primary-600 text-white"
            >
              {t('list.update')}
            </Link>
          </div>
        ),
      },
    ];
  }, [t]);

  return (
    <Layout>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('email-templates:list.title')}</h1>
        </div>

      </div>

      <DataTable
        title={t('email-templates:list.title')}
        count={count}
        pageSize={10}
        data={emailTemplates}
        columns={columns}
        sorting={sorting}
        onSortingChange={onSortingChange}
        page={page}
        maxPage={maxPage}
        onPageChange={onPageChange}
      />

    </Layout>
  );
};

export default EmailTemplates;
