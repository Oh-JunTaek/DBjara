# Changelog

DBjara 프로젝트의 모든 주요 변경 사항을 기록합니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 따릅니다.

---

## [v1.0.0] - 2026-08-17

### 최초 릴리즈

**핵심 기능**
- 솔로 큐(1인) 매칭 실시간 감지 및 자동 취소 (LCU API 연동)
- 통제 강도 3단계 설정 (상: 실행 차단 / 중: 솔로 차단 / 하: 시간 제한)
- 야간 시간대(기본 23:00~07:00) 강제 게임 종료 (디비자라 모드)
- 동반자 OTP 인증 시스템 (Google Authenticator 연동, 선택 옵션)
- Watchdog 프로세스를 통한 작업 관리자 강제 종료 방지
- 윈도우 시작 프로그램 자동 등록

**부가 기능**
- Riot ID 등록 및 Match-V5 API 전적 교차 검증 모듈 (PC방 우회 감지 대비)
- GitHub Releases 기반 자동 업데이트 확인
- 비식별 익명 사용 통계 수집 (GA4 Measurement Protocol, 동의 기반)
- 다국어 지원 (한국어 / English) - i18n 모듈 분리 설계
- 단일 실행 파일(.exe) 빌드 스크립트 및 GitHub Actions CI/CD 워크플로우

**개발 환경**
- Python 3.11 / Tkinter 다크 테마 GUI
- pystray, pillow, psutil, qrcode 의존성
- .gitignore, config.example.json 템플릿 제공

---

## [Unreleased] - 개발 예정

아래 항목들은 향후 버전에서 순차적으로 구현될 예정입니다.
상세 내용은 [ROADMAP.md](./ROADMAP.md)를 참조하세요.

- 보증금 챌린지 시스템 (Stripe/토스페이먼츠 결제 연동)
- 디스코드 웹훅 친구방 자동 알림
- Riot API 전적 검증 자동화 스케줄러
- 통계 대시보드 (웹 UI)
