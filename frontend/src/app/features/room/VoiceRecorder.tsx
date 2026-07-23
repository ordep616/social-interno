import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Badge,
  Box,
  Chip,
  Icon,
  IconButton,
  Icons,
  ProgressBar,
  Spinner,
  Text,
  config,
  toRem,
} from 'folds';
import { UploadProgress } from 'matrix-js-sdk';
import { bytesToSize, millisecondsToMinutesAndSeconds } from '../../utils/common';

const MAX_RECORDING_MS = 5 * 60 * 1000;
const MAX_RECORDING_BYTES = 10 * 1000 * 1000;
const AUDIO_BITS_PER_SECOND = 64000;
const RECORDING_MIME_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/mp4;codecs=mp4a.40.2',
  'audio/mp4',
  'audio/aac',
];

const getSupportedRecordingMimeType = (): string | undefined => {
  if (typeof MediaRecorder === 'undefined' || typeof MediaRecorder.isTypeSupported !== 'function') {
    return undefined;
  }
  return RECORDING_MIME_TYPES.find((mimeType) => MediaRecorder.isTypeSupported(mimeType));
};

const getAudioFileExtension = (mimeType: string): string => {
  const [type] = mimeType.split(';');
  if (type === 'audio/mp4') return 'm4a';
  if (type === 'audio/aac') return 'aac';
  if (type === 'audio/ogg') return 'ogg';
  return 'webm';
};

const createVoiceFileName = (mimeType: string): string => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return `voice-message-${timestamp}.${getAudioFileExtension(mimeType)}`;
};

const getRecordingErrorMessage = (error: unknown): string => {
  if (error instanceof DOMException) {
    if (error.name === 'NotAllowedError') return 'Permissao do microfone negada.';
    if (error.name === 'NotFoundError') return 'Nenhum microfone encontrado.';
  }
  if (error instanceof Error && error.message) return error.message;
  return 'Falha ao gravar audio.';
};

export type VoiceRecording = {
  file: File;
  duration: number;
  mimeType: string;
};

type VoiceRecorderStatus =
  | 'idle'
  | 'requesting'
  | 'recording'
  | 'paused'
  | 'stopping'
  | 'sending'
  | 'preview';

type VoiceRecorderProps = {
  disabled?: boolean;
  onSubmit: (
    recording: VoiceRecording,
    onProgress: (progress: UploadProgress) => void
  ) => Promise<void>;
};

export function VoiceRecorder({ disabled, onSubmit }: VoiceRecorderProps) {
  const mountedRef = useRef(true);
  const mediaRecorderRef = useRef<MediaRecorder | undefined>();
  const mediaStreamRef = useRef<MediaStream | undefined>();
  const chunksRef = useRef<Blob[]>([]);
  const activeStartedAtRef = useRef(0);
  const recordedMsRef = useRef(0);
  const stopActionRef = useRef<'cancel' | 'send'>('cancel');

  const [status, setStatus] = useState<VoiceRecorderStatus>('idle');
  const [elapsedMs, setElapsedMs] = useState(0);
  const [error, setError] = useState<string>();
  const [recording, setRecording] = useState<VoiceRecording>();
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>();

  const stopTracks = useCallback(() => {
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  const resetRecorderRefs = useCallback(() => {
    mediaRecorderRef.current = undefined;
    mediaStreamRef.current = undefined;
    chunksRef.current = [];
    activeStartedAtRef.current = 0;
    recordedMsRef.current = 0;
  }, []);

  const getCurrentElapsedMs = useCallback((): number => {
    const recorder = mediaRecorderRef.current;
    const activeStartedAt = activeStartedAtRef.current;
    const activeMs =
      recorder?.state === 'recording' && activeStartedAt > 0 ? Date.now() - activeStartedAt : 0;

    return recordedMsRef.current + activeMs;
  }, []);

  const reset = useCallback(() => {
    stopTracks();
    resetRecorderRefs();
    setElapsedMs(0);
    setRecording(undefined);
    setUploadProgress(undefined);
    setStatus('idle');
  }, [resetRecorderRefs, stopTracks]);

  const submitRecording = useCallback(
    async (voiceRecording: VoiceRecording) => {
      if (!mountedRef.current) return;

      setStatus('sending');
      setError(undefined);
      setUploadProgress(undefined);

      try {
        await onSubmit(voiceRecording, setUploadProgress);
        if (!mountedRef.current) return;
        reset();
      } catch (submitError) {
        if (!mountedRef.current) return;
        setRecording(voiceRecording);
        setStatus('preview');
        setError(getRecordingErrorMessage(submitError));
      }
    },
    [onSubmit, reset]
  );

  const stopAndSubmit = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === 'inactive') {
      if (recording) submitRecording(recording);
      return;
    }

    recordedMsRef.current = getCurrentElapsedMs();
    activeStartedAtRef.current = 0;
    stopActionRef.current = 'send';
    setStatus('sending');

    try {
      recorder.stop();
    } catch (stopError) {
      stopTracks();
      resetRecorderRefs();
      setStatus('idle');
      setError(getRecordingErrorMessage(stopError));
      return;
    }

    stopTracks();
  }, [getCurrentElapsedMs, recording, resetRecorderRefs, stopTracks, submitRecording]);

  const cancelRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    setError(undefined);
    setRecording(undefined);
    setUploadProgress(undefined);
    stopActionRef.current = 'cancel';

    if (!recorder || recorder.state === 'inactive') {
      reset();
      return;
    }

    setStatus('stopping');
    try {
      recorder.stop();
    } catch {
      reset();
      return;
    }
    stopTracks();
  }, [reset, stopTracks]);

  const pauseRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== 'recording') return;

    recordedMsRef.current = getCurrentElapsedMs();
    activeStartedAtRef.current = 0;
    recorder.pause();
    setElapsedMs(recordedMsRef.current);
    setStatus('paused');
  }, [getCurrentElapsedMs]);

  const resumeRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== 'paused') return;

    activeStartedAtRef.current = Date.now();
    recorder.resume();
    setStatus('recording');
  }, []);

  const startRecording = useCallback(async () => {
    if (disabled) return;

    setStatus('requesting');
    setError(undefined);
    setRecording(undefined);
    setUploadProgress(undefined);

    let stream: MediaStream | undefined;

    try {
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
        throw new Error('Gravacao de audio indisponivel neste navegador.');
      }

      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mountedRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      const mimeType = getSupportedRecordingMimeType();
      const recorderOptions: MediaRecorderOptions = {
        audioBitsPerSecond: AUDIO_BITS_PER_SECOND,
      };
      if (mimeType) recorderOptions.mimeType = mimeType;

      const recorder = new MediaRecorder(stream, recorderOptions);
      mediaStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];
      activeStartedAtRef.current = Date.now();
      recordedMsRef.current = 0;
      stopActionRef.current = 'cancel';
      setElapsedMs(0);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = (event) => {
        if (!mountedRef.current) return;
        stopTracks();
        resetRecorderRefs();
        setStatus('idle');
        setError(getRecordingErrorMessage(event.error));
      };

      recorder.onstop = () => {
        stopTracks();

        const action = stopActionRef.current;
        const duration = recordedMsRef.current;
        const chunks = chunksRef.current;
        const finalMimeType = recorder.mimeType || mimeType || 'audio/webm';

        resetRecorderRefs();

        if (!mountedRef.current) return;

        if (action === 'cancel') {
          setElapsedMs(0);
          setStatus('idle');
          return;
        }

        const blob = new Blob(chunks, { type: finalMimeType });
        if (blob.size === 0) {
          setStatus('idle');
          setError('Nenhum audio foi gravado.');
          return;
        }
        if (blob.size > MAX_RECORDING_BYTES) {
          setStatus('idle');
          setError(`Audio excede o limite de ${bytesToSize(MAX_RECORDING_BYTES)}.`);
          return;
        }

        const voiceRecording = {
          file: new File([blob], createVoiceFileName(finalMimeType), { type: finalMimeType }),
          duration,
          mimeType: finalMimeType,
        };
        setRecording(voiceRecording);
        submitRecording(voiceRecording);
      };

      recorder.start(1000);
      setStatus('recording');
    } catch (recordingError) {
      stream?.getTracks().forEach((track) => track.stop());
      resetRecorderRefs();
      setStatus('idle');
      setError(getRecordingErrorMessage(recordingError));
    }
  }, [disabled, resetRecorderRefs, stopTracks, submitRecording]);

  useEffect(() => {
    if (status !== 'recording') return undefined;

    const intervalId = window.setInterval(() => {
      const nextElapsedMs = getCurrentElapsedMs();
      setElapsedMs(nextElapsedMs);
      if (nextElapsedMs >= MAX_RECORDING_MS) {
        stopAndSubmit();
      }
    }, 250);

    return () => window.clearInterval(intervalId);
  }, [getCurrentElapsedMs, status, stopAndSubmit]);

  useEffect(
    () => () => {
      mountedRef.current = false;
      const recorder = mediaRecorderRef.current;
      stopActionRef.current = 'cancel';
      if (recorder && recorder.state !== 'inactive') {
        try {
          recorder.stop();
        } catch {
          // The component is unmounting, so the important part is releasing the stream.
        }
      }
      stopTracks();
    },
    [stopTracks]
  );

  const activeDuration = recording?.duration ?? elapsedMs;
  const uploading = status === 'sending';
  const uploadTotal = uploadProgress?.total ?? 0;
  const uploadLoaded = uploadProgress?.loaded ?? 0;

  if (status === 'idle') {
    return (
      <>
        <IconButton
          aria-label="Gravar mensagem de voz"
          onClick={startRecording}
          variant="SurfaceVariant"
          size="300"
          radii="300"
          disabled={disabled}
        >
          <Icon src={Icons.Mic} />
        </IconButton>
        {error && (
          <Chip
            as="button"
            onClick={() => setError(undefined)}
            variant="Critical"
            radii="Pill"
            outlined
          >
            <Text size="B300" truncate>
              {error}
            </Text>
          </Chip>
        )}
      </>
    );
  }

  return (
    <Box
      alignItems="Center"
      gap="100"
      style={{
        padding: `0 ${config.space.S100}`,
        minHeight: toRem(32),
      }}
    >
      {uploading || status === 'requesting' || status === 'stopping' ? (
        <Spinner variant="Secondary" size="100" />
      ) : (
        <Badge
          variant={status === 'paused' || status === 'preview' ? 'Warning' : 'Critical'}
          fill="Solid"
          radii="Pill"
        />
      )}
      <Text size="T200">{millisecondsToMinutesAndSeconds(activeDuration)}</Text>
      {status === 'preview' && error && (
        <Text size="T200" truncate style={{ maxWidth: toRem(160) }}>
          {error}
        </Text>
      )}
      {uploading && uploadTotal > 0 && (
        <Box style={{ width: toRem(64) }}>
          <ProgressBar
            variant="Secondary"
            size="300"
            min={0}
            max={uploadTotal}
            value={uploadLoaded}
            radii="300"
          />
        </Box>
      )}
      {status === 'recording' && (
        <IconButton
          aria-label="Pausar gravacao"
          onClick={pauseRecording}
          variant="SurfaceVariant"
          size="300"
          radii="300"
        >
          <Icon src={Icons.Pause} />
        </IconButton>
      )}
      {status === 'paused' && (
        <IconButton
          aria-label="Continuar gravacao"
          onClick={resumeRecording}
          variant="SurfaceVariant"
          size="300"
          radii="300"
        >
          <Icon src={Icons.Play} />
        </IconButton>
      )}
      {status === 'preview' && recording && (
        <Chip
          as="button"
          onClick={() => submitRecording(recording)}
          variant="Critical"
          radii="Pill"
        >
          <Text size="B300">Tentar novamente</Text>
        </Chip>
      )}
      {status !== 'requesting' && status !== 'sending' && status !== 'stopping' && (
        <>
          <IconButton
            aria-label="Cancelar gravacao"
            onClick={cancelRecording}
            variant="SurfaceVariant"
            size="300"
            radii="300"
          >
            <Icon src={Icons.Cross} />
          </IconButton>
          {status !== 'preview' && (
            <IconButton
              aria-label="Enviar mensagem de voz"
              onClick={stopAndSubmit}
              variant="Success"
              size="300"
              radii="300"
            >
              <Icon src={Icons.Send} />
            </IconButton>
          )}
        </>
      )}
    </Box>
  );
}
