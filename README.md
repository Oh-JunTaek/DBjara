# DBjara (디비자라) 2.0 - LoL 스마트 통제 솔루션

<div align="center">
  <img src="https://img.shields.io/badge/Release-v2.0.0-blue?style=flat-square&logo=github" alt="Release" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Riot%20Policy-Compliant-brightgreen?style=flat-square&logo=riotgames" alt="Riot Policy" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows" alt="Platform" />

  <p><strong>친구와의 게임은 즐겁게, 혼자만의 밤샘 솔랭은 강력하게 통제합니다.</strong></p>
  <p>복합 룰셋(Multi-Rule Matrix)과 행동경제학 기반 약정 시스템(Commitment Plan)이 적용된 모던 다크 통제 백그라운드 서비스</p>
</div>

---

## 주요 기능 (v2.0)

| 기능 | 설명 | 동작 방식 |
| :--- | :--- | :--- |
| **목표 약정 기간 (Commitment Plan)** | 1일 / 7일 / 30일 목표 잠금 | 약정 기간 동안 스스로 규칙을 완화하거나 바꿀 수 없도록 동반자 OTP로 잠급니다. |
| **1인 솔로 큐 독립 제어** | 솔로 랭크/솔로 큐 실시간 감시 | 상시 전면 차단 / 일일 시간 제한 / 무제한 중 원하는 제어 수준을 설정합니다. |
| **다인큐(파티) 독립 제어** | 친구와의 파티 플레이 시간 제한 | 무제한 / 일일 시간 제한 / 파티도 전면 차단 중 교집합 조건으로 제어합니다. |
| **스마트 멘탈 5분 휴식 쿨다운** | 게임 직후 연승/연패 뇌절 방지 | 한 판이 끝나면 5분간 큐를 돌릴 수 없게 쉬는 시간을 부여하여 연패 멘탈을 방지합니다. |
| **야간 강제 취침 (디비자라 모드)** | 지정된 야간 시간대 전면 차단 | 밤 11시 ~ 아침 7시(사용자 지정 가능)에 롤이 실행되면 즉시 프로세스를 강제 종료합니다. |
| **동반자 OTP 인증 시스템** | 제3자의 승인 없이는 변경/종료 불가 | 지인의 스마트폰 OTP 앱(Google Authenticator) 6자리 번호로 통제 권한을 부여합니다. |
| **익명 통계 & Riot ID 검증** | 차단 횟수 수집 및 외부 몰래 솔랭 방지 | 소환사 ID 등록 시 공식 Match API로 외부/PC방 몰래 솔랭 이력을 교차 검증합니다. |

---

## 프로젝트 문서

| 문서 | 설명 |
| :--- | :--- |
| [CHANGELOG.md](./CHANGELOG.md) | 버전별 변경 이력 |
| [ROADMAP.md](./ROADMAP.md) | 향후 업데이트 계획 및 기능 로드맵 |

---

## 라이선스

본 프로젝트는 MIT License를 따릅니다.
