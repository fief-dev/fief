import { html } from '@codemirror/lang-html';
import { ArrowLeftIcon, CheckIcon } from '@heroicons/react/20/solid';
import CodeMirror from '@uiw/react-codemirror';
import { githubDark } from '@uiw/codemirror-theme-github';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, LoaderFunction, useLoaderData, useNavigate } from 'react-router-dom';

import Layout from '../../components/Layout/Layout';
import { useAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import { APIClient } from '../../services/api';
import { useCallback } from 'react';
import LoadingSpinner from '../../components/LoadingSpinner/LoadingSpinner';

export const loader: LoaderFunction = async ({ params }): Promise<schemas.emailTemplate.EmailTemplate> => {
  const api = new APIClient();
  const { data: emailTemplate } = await api.getEmailTemplate(params.emailTemplateId as string);
  return emailTemplate;
}

const EditEmailTemplate: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const emailTemplate = useLoaderData() as schemas.emailTemplate.EmailTemplate;
  const navigate = useNavigate();
  const api = useAPI();
  const { t } = useTranslation(['email-templates']);

  const [content, setContent] = useState(emailTemplate.content);
  const [previewContent, setPreviewContent] = useState('');
  const [subject, setSubject] = useState(emailTemplate.subject);
  const [previewSubject, setPreviewSubject] = useState('');

  const [loadingPreview, setLoadingPreview] = useState(false);

  const onUpdate = useCallback(async () => {
    await api.updateEmailTemplate(emailTemplate.id, { content, subject });
    navigate('/email-templates');
  }, [api, emailTemplate, content, subject, navigate]);

  const preview = useCallback(async () => {
    setLoadingPreview(true);
    const { data: preview } = await api.previewEmailTemplate({ type: emailTemplate.type, content, subject });
    setPreviewContent(preview.content);
    setPreviewSubject(preview.subject);
    setLoadingPreview(false);
  }, [api, emailTemplate, content, subject]);

  useEffect(() => {
    let timeoutId = setTimeout(() => preview(), 1000);
    return () => window.clearTimeout(timeoutId);
  }, [preview]);

  return (
    <Layout>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('email-templates:edit.title', { type: t(`email_template_type.${emailTemplate.type}`) })}</h1>
        </div>

        <div className="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
          <Link
            to="/email-templates"
            className="btn border-slate-200 hover:border-slate-300 text-slate-600"
          >
            <ArrowLeftIcon width="16" height="16" />
            <span className="hidden xs:block ml-2">{t('email-templates:edit.back')}</span>
          </Link>
          <button
            type="button"
            className="btn bg-primary-500 hover:bg-primary-600 text-white"
            onClick={() => onUpdate()}
          >
            <CheckIcon width="16" height="16" />
            <span className="hidden xs:block ml-2">{t('email-templates:edit.update')}</span>
          </button>
        </div>

      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>

          <input
            className="form-input w-full mb-4"
            type="text"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
          />
          <div style={{ height: '75vh', overflow: 'auto' }}>
            <CodeMirror
              value={content}
              extensions={[html()]}
              theme={githubDark}
              onChange={(value) => setContent(value)}
            />
          </div>
        </div>
        <div className="h-full w-full relative">
          <input
            className="form-input w-full border-slate-200 disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed mb-4"
            disabled
            type="text"
            value={previewSubject}
          />
          <div style={{ height: '75vh', overflow: 'auto' }}>
            <iframe className="h-full w-full" title="Preview" srcDoc={previewContent} />
          </div>
          {loadingPreview &&
            <div className="absolute inset-0 bg-gray-300 w-full h-full flex justify-center items-center">
              <div className="w-6 h-6">
                <LoadingSpinner />
              </div>
            </div>
          }
        </div>
      </div>
    </Layout>
  );
};

export default EditEmailTemplate;
