/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Node, Edge } from './types';

export const MOCK_AIRPORTS: Node[] = [
  { id: 'PEK', name: 'Capital Intl', city: 'Beijing', lat: 40.0799, lng: 116.6031 },
  { id: 'PVG', name: 'Pudong Intl', city: 'Shanghai', lat: 31.1443, lng: 121.8083 },
  { id: 'CAN', name: 'Baiyun Intl', city: 'Guangzhou', lat: 23.3924, lng: 113.2988 },
  { id: 'SZX', name: 'Bao\'an Intl', city: 'Shenzhen', lat: 22.6393, lng: 113.8107 },
  { id: 'HGH', name: 'Xiaoshan Intl', city: 'Hangzhou', lat: 30.2295, lng: 120.4344 },
  { id: 'NKG', name: 'Lukou Intl', city: 'Nanjing', lat: 31.742, lng: 118.862 },
  { id: 'EHU', name: 'Huahu Airport', city: 'Ezhou', lat: 30.318, lng: 115.024 },
  { id: 'URC', name: 'Diwopu Intl', city: 'Urumqi', lat: 43.9071, lng: 87.4742 },
  { id: 'KMG', name: 'Changshui Intl', city: 'Kunming', lat: 25.1018, lng: 102.9292 },
  { id: 'CTU', name: 'Shuangliu Intl', city: 'Chengdu', lat: 30.5785, lng: 103.9471 },
  { id: 'TFU', name: 'Tianfu Intl', city: 'Chengdu', lat: 30.311, lng: 104.446 },
  { id: 'CGO', name: 'Xinzheng Intl', city: 'Zhengzhou', lat: 34.5197, lng: 113.8409 },
  { id: 'XIY', name: 'Xianyang Intl', city: 'Xi\'an', lat: 34.4471, lng: 108.7516 },
  { id: 'CKG', name: 'Jiangbei Intl', city: 'Chongqing', lat: 29.7192, lng: 106.6417 },
  { id: 'WUH', name: 'Tianhe Intl', city: 'Wuhan', lat: 30.7838, lng: 114.2081 },
  { id: 'CSX', name: 'Huanghua Intl', city: 'Changsha', lat: 28.1892, lng: 113.2197 },
  { id: 'HAK', name: 'Meilan Intl', city: 'Haikou', lat: 19.9349, lng: 110.459 },
  { id: 'DLC', name: 'Zhoushuizi Intl', city: 'Dalian', lat: 38.9656, lng: 121.5386 },
  { id: 'SHE', name: 'Taoxian Intl', city: 'Shenyang', lat: 41.6398, lng: 123.4834 },
  { id: 'HRB', name: 'Taiping Intl', city: 'Harbin', lat: 45.6234, lng: 126.2503 },
];

export const generateMockEdges = (): Edge[] => {
  const edges: Edge[] = [];
  const hubs = ['PEK', 'PVG', 'CAN', 'SZX', 'HGH', 'EHU', 'CGO'];
  
  // Connect hubs to each other
  for (let i = 0; i < hubs.length; i++) {
    for (let j = 0; j < hubs.length; j++) {
      if (i !== j) {
        edges.push({
          source: hubs[i],
          target: hubs[j],
          weight: Math.floor(Math.random() * 100) + 50
        });
      }
    }
  }

  // Connect regional airports to hubs
  const regional = MOCK_AIRPORTS.filter(a => !hubs.includes(a.id));
  regional.forEach(r => {
    // Each regional airport connects to 2-4 random hubs
    const count = Math.floor(Math.random() * 3) + 2;
    const selectedHubs = [...hubs].sort(() => Math.random() - 0.5).slice(0, count);
    selectedHubs.forEach(h => {
      edges.push({
        source: r.id,
        target: h,
        weight: Math.floor(Math.random() * 50) + 10
      });
      edges.push({
        source: h,
        target: r.id,
        weight: Math.floor(Math.random() * 50) + 10
      });
    });
  });

  // Special connections mentioned in the paper
  // EHU as a new hub
  const ehuConnections = ['HGH', 'SZX', 'CAN', 'PEK', 'PVG', 'WUH', 'URC'];
  ehuConnections.forEach(target => {
    if (!edges.find(e => e.source === 'EHU' && e.target === target)) {
      edges.push({ source: 'EHU', target, weight: 80 });
      edges.push({ source: target, target: 'EHU', weight: 80 });
    }
  });

  return edges;
};
