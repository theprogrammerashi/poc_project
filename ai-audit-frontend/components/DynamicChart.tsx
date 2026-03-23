"use client";
import React from 'react';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    AreaChart, Area, ScatterChart, Scatter,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

type ChartProps = {
    type: 'bar' | 'line' | 'pie' | 'area' | 'scatter';
    data: any[];
    xKey: string;
    yKey: string;
};

const COLORS = ['#E8400C', '#2563EB', '#F59E0B', '#10B981', '#7C3AED', '#D946EF', '#EC4899', '#06B6D4'];

export default function DynamicChart({ type, data, xKey, yKey }: ChartProps) {
    if (!data || data.length === 0) return null;

    const renderChart = () => {
        switch (type) {
            case 'bar':
                return (
                    <BarChart data={data} margin={{ top: 20, right: 10, left: -20, bottom: 0 }} barSize={32}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
                        <XAxis dataKey={xKey} stroke="#9ca3af" axisLine={false} tickLine={false} dy={10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <YAxis stroke="#9ca3af" axisLine={false} tickLine={false} dx={-10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <Tooltip cursor={{ fill: '#F9FAFB' }} contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Bar dataKey={yKey} radius={[4, 4, 0, 0]}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Bar>
                    </BarChart>
                );
            case 'line':
            case 'area':
                return (
                    <AreaChart data={data} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#E8400C" stopOpacity={0.15}/>
                                <stop offset="95%" stopColor="#E8400C" stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={true} />
                        <XAxis dataKey={xKey} stroke="#9ca3af" axisLine={false} tickLine={false} dy={10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <YAxis stroke="#9ca3af" axisLine={false} tickLine={false} dx={-10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Area 
                            type="monotone" 
                            dataKey={yKey} 
                            stroke="#E8400C" 
                            strokeWidth={3} 
                            fill="url(#colorGradient)" 
                            activeDot={{ r: 6, fill: '#E8400C', stroke: '#fff', strokeWidth: 2 }} 
                            dot={{ r: 5, fill: '#E8400C', strokeWidth: 2, stroke: '#fff' }} 
                        />
                    </AreaChart>
                );
            case 'pie':
                return (
                    <PieChart margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                        <Pie data={data} cx="50%" cy="50%" labelLine={false} outerRadius={100} innerRadius={60} fill="#8884d8" dataKey={yKey} nameKey={xKey} stroke="none" paddingAngle={2} cornerRadius={4}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} itemStyle={{ color: '#1F2937' }} />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
                    </PieChart>
                );
            case 'scatter':
                return (
                    <ScatterChart margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={true} />
                        <XAxis type="category" dataKey={xKey} name={xKey} stroke="#9ca3af" axisLine={false} tickLine={false} dy={10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <YAxis type="number" dataKey={yKey} name={yKey} stroke="#9ca3af" axisLine={false} tickLine={false} dx={-10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Scatter name={yKey} data={data} fill="#E8400C" shape="circle" />
                    </ScatterChart>
                );
            default:
                return null;
        }
    };

    const [mounted, setMounted] = React.useState(false);
    React.useEffect(() => setMounted(true), []);

    if (!mounted) {
        return <div className="w-full h-[260px] mt-2 bg-gray-50/50 animate-pulse rounded-xl" />;
    }

    return (
        <div className="w-full h-[260px] mt-2">
            <ResponsiveContainer width="100%" height="100%">
                {renderChart()}
            </ResponsiveContainer>
        </div>
    );
}