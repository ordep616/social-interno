/* eslint-disable jsx-a11y/media-has-caption */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Icon, Icons, Spinner, Text } from 'folds';
import { EncryptedAttachmentInfo } from 'browser-encrypt-attachment';
import { Range } from 'react-range';
import { useMatrixClient } from '../../../hooks/useMatrixClient';
import { AsyncStatus, useAsyncCallback } from '../../../hooks/useAsyncCallback';
import { IAudioInfo } from '../../../../types/matrix/common';
import {
  PlayTimeCallback,
  useMediaLoading,
  useMediaPlay,
  useMediaPlayTimeCallback,
  useMediaSeek,
} from '../../../hooks/media';
import { useThrottle } from '../../../hooks/useThrottle';
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

const PLAY_TIME_THROTTLE_OPS = {
  wait: 500,
  immediate: true,
};

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

export type AudioContentProps = {
  mimeType: string;
  url: string;
  info: IAudioInfo;
  encInfo?: EncryptedAttachmentInfo;
  displayName: string;
  ts: number;
  senderIsMe?: boolean;
};
export function AudioContent({
  mimeType,
  url,
  info,
  encInfo,
  displayName,
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

  const [currentTime, setCurrentTime] = useState(0);
  // duration in seconds. (NOTE: info.duration is in milliseconds)
  const infoDuration = info.duration ?? 0;
  const [duration, setDuration] = useState((infoDuration >= 0 ? infoDuration : 0) / 1000);

  const getAudioRef = useCallback(() => audioRef.current, []);
  const { loading, error: mediaError } = useMediaLoading(getAudioRef);
  const { playing, setPlaying } = useMediaPlay(getAudioRef);
  const { seek } = useMediaSeek(getAudioRef);
  const handlePlayTimeCallback: PlayTimeCallback = useCallback((d, ct) => {
    if (Number.isFinite(d)) setDuration(d);
    setCurrentTime(ct);
  }, []);
  useMediaPlayTimeCallback(
    getAudioRef,
    useThrottle(handlePlayTimeCallback, PLAY_TIME_THROTTLE_OPS)
  );

  useEffect(() => {
    if (srcState.status !== AsyncStatus.Success) return undefined;
    const { src } = srcState.data as AudioContentData;
    return () => URL.revokeObjectURL(src);
  }, [srcState]);

  const handlePlay = () => {
    if (srcState.status === AsyncStatus.Success) {
      setPlaying(!playing);
    } else if (srcState.status !== AsyncStatus.Loading) {
      loadSrc().catch(() => undefined);
    }
  };

  const waveform =
    srcState.status === AsyncStatus.Success
      ? (srcState.data as AudioContentData).waveform
      : FALLBACK_WAVEFORM;
  const safeDuration = duration || 1;
  const activeBars = Math.round((currentTime / safeDuration) * waveform.length);
  const sentAt = timeHourMinute(ts, true);
  const sourceUrl =
    srcState.status === AsyncStatus.Success ? (srcState.data as AudioContentData).src : undefined;
  const hasError = srcState.status === AsyncStatus.Error || mediaError;
  const ariaLabel = useMemo(
    () => `Mensagem de voz de ${displayName} as ${sentAt}`,
    [displayName, sentAt]
  );

  return (
    <div className={css.VoiceMessage} data-own={senderIsMe ? 'true' : 'false'}>
      <div className={css.VoiceMeta}>
        <Text className={css.VoiceSender} as="span" size="B300" truncate>
          {displayName}
        </Text>
        <Text className={css.VoiceTime} as="time" size="T200">
          {sentAt}
        </Text>
      </div>
      <div className={css.VoiceBody}>
        <button
          className={css.PlayButton}
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
            values={[Math.min(currentTime, safeDuration)]}
            onChange={(values) => seek(values[0])}
            renderTrack={(params) => (
              <div {...params.props} className={css.WaveformTrack} style={params.props.style}>
                {waveform.map((peak, index) => (
                  <span
                    // eslint-disable-next-line react/no-array-index-key
                    key={index}
                    className={css.WaveformBar}
                    data-active={index < activeBars ? 'true' : 'false'}
                    style={{ height: `${Math.round(4 + peak * 24)}px` }}
                  />
                ))}
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
            <Text as="span" size="T200">
              {secondsToMinutesAndSeconds(duration)}
            </Text>
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
        autoPlay
        ref={audioRef}
        src={sourceUrl}
      />
    </div>
  );
}
