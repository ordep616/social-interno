/* eslint-disable jsx-a11y/media-has-caption */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Icon, Icons, Spinner, Text } from 'folds';
import { EncryptedAttachmentInfo } from 'browser-encrypt-attachment';
import { Range } from 'react-range';
import { useMatrixClient } from '../../../hooks/useMatrixClient';
import { AsyncStatus, useAsyncCallback } from '../../../hooks/useAsyncCallback';
import { IAudioInfo } from '../../../../types/matrix/common';
import { useMediaLoading, useMediaPlay, useMediaSeek } from '../../../hooks/media';
import { secondsToMinutesAndSeconds } from '../../../utils/common';
import {
  decryptFile,
  downloadEncryptedMedia,
  downloadMedia,
  mxcUrlToHttp,
} from '../../../utils/matrix';
import { useMediaAuthentication } from '../../../hooks/useMediaAuthentication';
import { timeHourMinute } from '../../../utils/time';
import * as css from './AudioContent.css';

let activeVoiceAudioElement: HTMLAudioElement | undefined;

const TIMELINE_MESSAGE_SELECTOR = '[data-message-item]';
const VOICE_AUDIO_PLAYER_SELECTOR = '[data-voice-audio-player=true]';
const VOICE_AUDIO_PLAY_BUTTON_SELECTOR = '[data-voice-audio-play-button=true]';
const VOICE_PLAYBACK_RATES = [1, 1.5, 2] as const;

type VoicePlaybackRate = typeof VOICE_PLAYBACK_RATES[number];

let voicePlaybackRate: VoicePlaybackRate = 1;
const voicePlaybackRateListeners = new Set<(rate: VoicePlaybackRate) => void>();

const WAVEFORM_BAR_COUNT = 34;
const MIN_BAR_SCALE = 0.16;
const FALLBACK_WAVEFORM = [
  0.22, 0.26, 0.33, 0.29, 0.45, 0.68, 0.42, 0.3, 0.72, 0.86, 0.52, 0.38, 0.28, 0.34, 0.59, 0.77,
  0.92, 0.83, 0.74, 0.62, 0.48, 0.36, 0.42, 0.66, 0.9, 0.7, 0.54, 0.4, 0.32, 0.28, 0.46, 0.61, 0.37,
  0.24,
];

type AudioContentData = {
  src: string;
  waveform: number[];
};

type AudioContextWindow = Window &
  typeof globalThis & {
    webkitAudioContext?: typeof AudioContext;
  };

const getAudioContext = (): AudioContext | undefined => {
  const AudioContextConstructor =
    window.AudioContext ?? (window as AudioContextWindow).webkitAudioContext;
  return AudioContextConstructor ? new AudioContextConstructor() : undefined;
};

const getWaveformPeaks = async (fileContent: Blob): Promise<number[]> => {
  const audioContext = getAudioContext();
  if (!audioContext) return FALLBACK_WAVEFORM;

  try {
    const audioBuffer = await audioContext.decodeAudioData(await fileContent.arrayBuffer());
    const peaks = Array.from({ length: WAVEFORM_BAR_COUNT }, (_, barIndex) => {
      const start = Math.floor((barIndex / WAVEFORM_BAR_COUNT) * audioBuffer.length);
      const end = Math.max(
        start + 1,
        Math.floor(((barIndex + 1) / WAVEFORM_BAR_COUNT) * audioBuffer.length)
      );
      const stride = Math.max(1, Math.floor((end - start) / 1200));
      let peak = 0;

      for (let channel = 0; channel < audioBuffer.numberOfChannels; channel += 1) {
        const data = audioBuffer.getChannelData(channel);
        for (let index = start; index < end; index += stride) {
          peak = Math.max(peak, Math.abs(data[index]));
        }
      }

      return peak;
    });
    const maxPeak = Math.max(...peaks, MIN_BAR_SCALE);
    return peaks.map((peak) => Math.max(MIN_BAR_SCALE, Math.min(1, peak / maxPeak)));
  } finally {
    await audioContext.close().catch(() => undefined);
  }
};

const clampProgress = (value: number): number => Math.max(0, Math.min(1, value));

const getFiniteDuration = (duration: number | undefined): number | undefined =>
  typeof duration === 'number' && Number.isFinite(duration) && duration > 0 ? duration : undefined;

const getPlaybackRateLabel = (rate: VoicePlaybackRate): string => `${rate}x`;

const getNextPlaybackRate = (rate: VoicePlaybackRate): VoicePlaybackRate => {
  const rateIndex = VOICE_PLAYBACK_RATES.indexOf(rate);
  return VOICE_PLAYBACK_RATES[(rateIndex + 1) % VOICE_PLAYBACK_RATES.length];
};

const setVoicePlaybackRate = (rate: VoicePlaybackRate): void => {
  voicePlaybackRate = rate;
  voicePlaybackRateListeners.forEach((listener) => listener(rate));
};

const getNextTimelineMessageElement = (messageElement: Element): HTMLElement | undefined => {
  let nextElement = messageElement.nextElementSibling;
  while (nextElement) {
    if (nextElement instanceof HTMLElement && nextElement.matches(TIMELINE_MESSAGE_SELECTOR)) {
      return nextElement;
    }
    nextElement = nextElement.nextElementSibling;
  }
  return undefined;
};

const playNextReadyVoiceMessage = (rootElement: HTMLElement | null, senderId?: string): void => {
  if (!rootElement || !senderId) return;

  const messageElement = rootElement.closest(TIMELINE_MESSAGE_SELECTOR);
  if (!messageElement) return;

  const nextMessageElement = getNextTimelineMessageElement(messageElement);
  const nextVoiceElement = nextMessageElement?.querySelector<HTMLElement>(
    VOICE_AUDIO_PLAYER_SELECTOR
  );
  if (
    !nextVoiceElement ||
    nextVoiceElement.dataset.voiceSenderId !== senderId ||
    nextVoiceElement.dataset.voiceReady !== 'true'
  ) {
    return;
  }

  const nextPlayButton = nextVoiceElement.querySelector<HTMLButtonElement>(
    VOICE_AUDIO_PLAY_BUTTON_SELECTOR
  );
  if (!nextPlayButton || nextPlayButton.disabled) return;

  nextPlayButton.click();
};

export type AudioContentProps = {
  mimeType: string;
  url: string;
  info: IAudioInfo;
  encInfo?: EncryptedAttachmentInfo;
  displayName: string;
  senderId?: string;
  ts: number;
  senderIsMe?: boolean;
};
export function AudioContent({
  mimeType,
  url,
  info,
  encInfo,
  displayName,
  senderId,
  ts,
  senderIsMe,
}: AudioContentProps) {
  const mx = useMatrixClient();
  const useAuthentication = useMediaAuthentication();

  const [srcState, loadSrc] = useAsyncCallback(
    useCallback(async () => {
      const mediaUrl = mxcUrlToHttp(mx, url, useAuthentication);
      if (!mediaUrl) throw new Error('Invalid media URL');
      const fileContent = encInfo
        ? await downloadEncryptedMedia(mediaUrl, (encBuf) => decryptFile(encBuf, mimeType, encInfo))
        : await downloadMedia(mediaUrl);
      const waveform = await getWaveformPeaks(fileContent).catch(() => FALLBACK_WAVEFORM);
      return {
        src: URL.createObjectURL(fileContent),
        waveform,
      };
    }, [mx, url, useAuthentication, mimeType, encInfo])
  );

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rootRef = useRef<HTMLDivElement | null>(null);

  const [currentTime, setCurrentTime] = useState(0);
  const [playbackRate, setPlaybackRate] = useState<VoicePlaybackRate>(voicePlaybackRate);
  // duration in seconds. (NOTE: info.duration is in milliseconds)
  const infoDuration = info.duration ?? 0;
  const infoDurationSeconds = (infoDuration >= 0 ? infoDuration : 0) / 1000;
  const [duration, setDuration] = useState(infoDurationSeconds);

  const getAudioRef = useCallback(() => audioRef.current, []);
  const { loading, error: mediaError } = useMediaLoading(getAudioRef);
  const { playing, setPlaying } = useMediaPlay(getAudioRef);
  const { seek } = useMediaSeek(getAudioRef);
  const sourceUrl =
    srcState.status === AsyncStatus.Success ? (srcState.data as AudioContentData).src : undefined;
  const playbackRateLabel = getPlaybackRateLabel(playbackRate);

  const syncAudioProgress = useCallback(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;

    const nextDuration =
      getFiniteDuration(audioElement.duration) ?? getFiniteDuration(infoDurationSeconds) ?? 0;
    const nextCurrentTime = audioElement.ended
      ? nextDuration
      : Math.min(audioElement.currentTime, nextDuration || audioElement.currentTime);

    setDuration(nextDuration);
    setCurrentTime(nextCurrentTime);
  }, [infoDurationSeconds]);

  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return undefined;

    audioElement.addEventListener('durationchange', syncAudioProgress);
    audioElement.addEventListener('loadedmetadata', syncAudioProgress);
    audioElement.addEventListener('seeked', syncAudioProgress);
    audioElement.addEventListener('timeupdate', syncAudioProgress);
    audioElement.addEventListener('ended', syncAudioProgress);

    return () => {
      audioElement.removeEventListener('durationchange', syncAudioProgress);
      audioElement.removeEventListener('loadedmetadata', syncAudioProgress);
      audioElement.removeEventListener('seeked', syncAudioProgress);
      audioElement.removeEventListener('timeupdate', syncAudioProgress);
      audioElement.removeEventListener('ended', syncAudioProgress);
    };
  }, [sourceUrl, syncAudioProgress]);

  useEffect(() => {
    if (!playing) return undefined;

    let animationFrameId = 0;
    const syncPlayProgress = () => {
      syncAudioProgress();
      animationFrameId = window.requestAnimationFrame(syncPlayProgress);
    };

    animationFrameId = window.requestAnimationFrame(syncPlayProgress);
    return () => window.cancelAnimationFrame(animationFrameId);
  }, [playing, syncAudioProgress]);

  useEffect(() => {
    const handlePlaybackRateChange = (rate: VoicePlaybackRate) => {
      setPlaybackRate(rate);
    };

    voicePlaybackRateListeners.add(handlePlaybackRateChange);
    return () => {
      voicePlaybackRateListeners.delete(handlePlaybackRateChange);
    };
  }, []);

  useEffect(() => {
    const audioElement = audioRef.current;
    if (audioElement) {
      audioElement.playbackRate = playbackRate;
    }
  }, [playbackRate, sourceUrl]);

  useEffect(() => {
    if (srcState.status === AsyncStatus.Idle) {
      loadSrc().catch(() => undefined);
    }
  }, [loadSrc, srcState.status]);

  useEffect(() => {
    if (srcState.status !== AsyncStatus.Success) return undefined;
    const { src } = srcState.data as AudioContentData;
    return () => URL.revokeObjectURL(src);
  }, [srcState]);

  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return undefined;

    const handlePlayStart = () => {
      const previousAudioElement = activeVoiceAudioElement;
      activeVoiceAudioElement = audioElement;

      if (previousAudioElement && previousAudioElement !== audioElement) {
        previousAudioElement.pause();
      }
    };
    const handlePlayStop = () => {
      if (activeVoiceAudioElement === audioElement) {
        activeVoiceAudioElement = undefined;
      }
    };
    const handlePlayEnd = () => {
      handlePlayStop();
      playNextReadyVoiceMessage(rootRef.current, senderId);
    };

    audioElement.addEventListener('play', handlePlayStart);
    audioElement.addEventListener('pause', handlePlayStop);
    audioElement.addEventListener('ended', handlePlayEnd);

    return () => {
      audioElement.removeEventListener('play', handlePlayStart);
      audioElement.removeEventListener('pause', handlePlayStop);
      audioElement.removeEventListener('ended', handlePlayEnd);
      if (activeVoiceAudioElement === audioElement) {
        activeVoiceAudioElement = undefined;
      }
    };
  }, [senderId]);

  const handlePlay = () => {
    if (srcState.status === AsyncStatus.Success) {
      const audioElement = audioRef.current;
      if (!playing && audioElement?.ended) {
        audioElement.currentTime = 0;
      }
      setPlaying(!playing);
    } else if (srcState.status !== AsyncStatus.Loading) {
      loadSrc().catch(() => undefined);
    }
  };

  const handlePlaybackRate = () => {
    setVoicePlaybackRate(getNextPlaybackRate(playbackRate));
  };

  const waveform =
    srcState.status === AsyncStatus.Success
      ? (srcState.data as AudioContentData).waveform
      : FALLBACK_WAVEFORM;
  const playbackDuration = getFiniteDuration(duration) ?? getFiniteDuration(infoDurationSeconds);
  const safeDuration = playbackDuration ?? 1;
  const safeCurrentTime = Math.min(currentTime, safeDuration);
  const progress = playbackDuration ? clampProgress(safeCurrentTime / playbackDuration) : 0;
  const progressClipRight = `${100 - progress * 100}%`;
  const sentAt = timeHourMinute(ts, true);
  const hasError = srcState.status === AsyncStatus.Error || mediaError;
  const ariaLabel = useMemo(
    () => `Mensagem de voz de ${displayName} as ${sentAt}`,
    [displayName, sentAt]
  );

  return (
    <div
      ref={rootRef}
      className={css.VoiceMessage}
      data-own={senderIsMe ? 'true' : 'false'}
      data-voice-audio-player="true"
      data-voice-ready={srcState.status === AsyncStatus.Success ? 'true' : 'false'}
      data-voice-sender-id={senderId}
    >
      <div className={css.VoiceBody}>
        <button
          className={css.PlayButton}
          data-voice-audio-play-button="true"
          type="button"
          onClick={handlePlay}
          disabled={srcState.status === AsyncStatus.Loading || loading}
          aria-label={playing ? 'Pausar audio' : 'Reproduzir audio'}
          aria-pressed={playing}
          title={playing ? 'Pausar' : 'Reproduzir'}
        >
          {srcState.status === AsyncStatus.Loading || loading ? (
            <Spinner size="100" />
          ) : (
            <Icon src={playing ? Icons.Pause : Icons.Play} size="200" filled />
          )}
        </button>
        <div className={css.Timeline}>
          <Range
            step={0.1}
            min={0}
            max={safeDuration}
            values={[safeCurrentTime]}
            onChange={(values) => seek(values[0])}
            renderTrack={(params) => (
              <div {...params.props} className={css.WaveformTrack} style={params.props.style}>
                {waveform.map((peak, index) => (
                  <span
                    // eslint-disable-next-line react/no-array-index-key
                    key={index}
                    className={css.WaveformBar}
                    style={{ height: `${Math.round(4 + peak * 24)}px` }}
                  />
                ))}
                <div
                  className={css.WaveformProgress}
                  style={{ clipPath: `inset(0 ${progressClipRight} 0 0)` }}
                  aria-hidden
                >
                  {waveform.map((peak, index) => (
                    <span
                      // eslint-disable-next-line react/no-array-index-key
                      key={index}
                      className={css.WaveformProgressBar}
                      style={{ height: `${Math.round(4 + peak * 24)}px` }}
                    />
                  ))}
                </div>
                {params.children}
              </div>
            )}
            renderThumb={(params) => (
              <span
                {...params.props}
                aria-label={ariaLabel}
                className={css.WaveformThumb}
                style={params.props.style}
              />
            )}
          />
          <div className={css.TimeRow}>
            <Text as="span" size="T200">
              {secondsToMinutesAndSeconds(currentTime)}
            </Text>
            <div className={css.TimeAfter}>
              <Text as="span" size="T200">
                {secondsToMinutesAndSeconds(duration)}
              </Text>
              <button
                className={css.PlaybackRateButton}
                type="button"
                onClick={handlePlaybackRate}
                aria-label={`Alterar velocidade do audio. Atual: ${playbackRateLabel}`}
                title={`Velocidade ${playbackRateLabel}`}
              >
                <Text as="span" size="B300">
                  {playbackRateLabel}
                </Text>
              </button>
            </div>
          </div>
        </div>
      </div>
      {hasError && (
        <Text className={css.ErrorText} as="div" size="T200" role="alert">
          Falha ao carregar audio.
        </Text>
      )}
      <audio
        className={css.AudioElement}
        controls={false}
        preload="metadata"
        ref={audioRef}
        src={sourceUrl}
      />
    </div>
  );
}
