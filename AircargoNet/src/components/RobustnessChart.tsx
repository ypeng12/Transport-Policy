/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { RobustnessPoint } from '../types';

interface Props {
  data: RobustnessPoint[][];
}

export const RobustnessChart: React.FC<Props> = ({ data }) => {
  // Flatten and combine data for Recharts
  // Recharts expects an array of objects where each object has values for all series at a given X
  const combinedData: any[] = [];
  if (data.length > 0) {
    const steps = data[0].length;
    for (let i = 0; i < steps; i++) {
      const point: any = { ratio: data[0][i].removalRatio };
      data.forEach(series => {
        if (series[i]) {
          point[series[i].strategy] = series[i].ngc;
        }
      });
      combinedData.push(point);
    }
  }

  const colors = {
    random: '#94a3b8',
    degree: '#6366f1',
    betweenness: '#f59e0b',
    pageRank: '#ec4899',
    domiRank: '#10b981'
  };

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={combinedData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis 
            dataKey="ratio" 
            label={{ value: 'Removal Ratio', position: 'insideBottom', offset: -5 }} 
            tickFormatter={(v) => v.toFixed(1)}
          />
          <YAxis label={{ value: 'NGC Size', angle: -90, position: 'insideLeft' }} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
            formatter={(value: number) => value.toFixed(3)}
          />
          <Legend verticalAlign="top" height={36}/>
          {Object.entries(colors).map(([strategy, color]) => (
            <Line 
              key={strategy}
              type="monotone" 
              dataKey={strategy} 
              stroke={color} 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
