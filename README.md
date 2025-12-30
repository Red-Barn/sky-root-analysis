## sky-root-analysis
프로젝트 하늘길 데이터 분석

## 🔍 Overview
인천국제공항 이용객들을 위한 최적화 경로와 실시간 정보를 제공하기 위한 프로젝트의 데이터 분석 부분입니다.
Pytorch의 GRU 모델을 사용해 유동인구의 인구수를 예측했습니다.
유동인구의 좌표와 각 정류장의 좌표를 통해 이용한 대중교통 및 경로를 구할 때 CPU 연산으로는 너무 느려 PyTorch 텐서를 활용해 GPU 병렬 연산으로 최적화한 프로젝트입니다.

## ✨ Features
- PyTorch Tensor 기반 병렬 연산
- GRU 모델을 사용한 인구수 예측
- 대규모 데이터 전처리

## 📁 Project Structure
(위에서 만든 폴더 구조 설명)

## 📦 Requirements
Python 3
PyTorch 3.10.13

## 🚀 How to Run