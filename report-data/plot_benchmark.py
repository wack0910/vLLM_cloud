"""Report plots from official vLLM bench JSON; authored for this task.
Usage: python report-data/plot_benchmark.py input.json output_directory
Requires matplotlib and numpy. No vLLM package or GPU required.
"""
from pathlib import Path
import argparse
import csv
import json
import math
import statistics
import sys

local_deps = Path(__file__).resolve().parents[1] / '.plot-deps'
if local_deps.exists():
    sys.path.insert(0, str(local_deps))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input_json', type=Path)
    p.add_argument('output_dir', type=Path)
    p.add_argument('--english', action='store_true', help='Force English chart labels.')
    args = p.parse_args()
    d = json.loads(args.input_json.read_text(encoding='utf-8'))
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    has_cjk = False
    font = Path('C:/Windows/Fonts/malgun.ttf')
    if not args.english and font.exists():
        font_manager.fontManager.addfont(str(font))
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(font)).get_name()
        has_cjk = True
    elif not args.english:
        for candidate in ('Noto Sans CJK KR', 'Noto Sans CJK JP', 'NanumGothic', 'Source Han Sans KR'):
            if any(item.name == candidate for item in font_manager.fontManager.ttflist):
                plt.rcParams['font.family'] = candidate
                has_cjk = True
                break
    translations = {
        '기준 측정 |': 'Benchmark |',
        '요청별 응답 지연': 'Request latency',
        '생성 지연: 중앙값과 P95': 'Generation latency: P50 and P95',
        '밀리초 (ms)': 'Milliseconds (ms)',
        '초 (s)': 'Seconds (s)',
        '스트리밍 간격 분포': 'Observed streaming intervals',
        '관측된 ITL (ms)': 'Observed ITL (ms)',
        '관측 간격 수': 'Interval count',
        '요청별 첫 토큰 대기': 'Time to first token by request',
        '요청 번호 (저장 순서)': 'Request ID (saved order)',
        '요청 실행 타임라인 | 클라이언트 전송 전 대기는 표시하지 않음':
            'Request timeline | client queue before send is excluded',
        '전송 시작 → 첫 토큰 (TTFT)': 'Send start to first token (TTFT)',
        '첫 토큰 → 응답 완료': 'First token to completion',
        '첫 요청 전송 시작 기준 시간 (s)': 'Seconds since first request send',
    }
    def localize(figure):
        if not has_cjk:
            for text in figure.findobj(match=matplotlib.text.Text):
                value = text.get_text()
                for original, translated in translations.items():
                    value = value.replace(original, translated)
                text.set_text(value)

    plt.rcParams.update({'axes.unicode_minus': False, 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    n = len(d['ttfts'])
    assert n == d['completed'] == len(d['latencies']) == len(d['output_lens'])
    assert sum(d['input_lens']) == d['total_input_tokens']
    assert sum(d['output_lens']) == d['total_output_tokens']
    ttft = np.asarray(d['ttfts'])
    latency = np.asarray(d['latencies'])
    output_lens = np.asarray(d['output_lens'])
    tpot = (latency-ttft)/(output_lens-1)*1000
    itl = np.asarray([v for row in d['itls'] for v in row])*1000
    starts = np.asarray(d['start_times'])-min(d['start_times'])
    assert math.isclose(float(np.mean(tpot)), d['mean_tpot_ms'], abs_tol=1e-6)
    for key, array in [('ttft',ttft*1000),('tpot',tpot),('itl',itl),('e2el',latency*1000)]:
        for percentile in (50,95):
            assert math.isclose(float(np.percentile(array,percentile)),d[f'p{percentile}_{key}_ms'],abs_tol=1e-6)
    teal, orange = '#157F79','#C76B2B'
    fig, axes = plt.subplots(2,2,figsize=(12,8.2),layout='constrained')
    fig.suptitle('기준 측정 | Qwen3.8-27B-FP8',fontsize=18,fontweight='bold')
    fig.supxlabel(f"100 requests · target input/output 3072/256 · concurrency 32\n"
                  f"{d['duration']:.2f} s · {d['output_throughput']:.2f} output token/s · failed {d['failed']}",fontsize=10)
    panels = [(axes[0,0],['TTFT','E2EL'],['ttft','e2el'],1000,'초 (s)','요청별 응답 지연'),
              (axes[0,1],['TPOT','ITL'],['tpot','itl'],1,'밀리초 (ms)','생성 지연: 중앙값과 P95')]
    for ax, names, keys, scale, ylabel, title in panels:
        x = np.arange(2)
        for delta, percentile, color in [(-.18,50,teal),(.18,95,orange)]:
            values=[d[f'p{percentile}_{key}_ms']/scale for key in keys]
            bars=ax.bar(x+delta,values,width=.34,label=f'P{percentile}',color=color)
            ax.bar_label(bars,labels=[f'{v:.2f}' for v in values],padding=4,fontsize=10)
        ax.set_xticks(x,names)
        ax.set_ylabel(ylabel)
        ax.set_title(title,fontweight='bold')
        ax.set_ylim(0,ax.get_ylim()[1]*1.15)
        ax.grid(axis='y',alpha=.18)
        ax.set_axisbelow(True)
        ax.legend(frameon=False)
    ax=axes[1,0]
    ax.hist(itl,bins=np.linspace(0,max(1000,itl.max()+1),51),color=teal)
    ax.axvline(d['p95_itl_ms'],color=orange,linestyle='--',label=f"P95 {d['p95_itl_ms']:.2f} ms")
    ax.set(title='스트리밍 간격 분포',xlabel='관측된 ITL (ms)',ylabel='관측 간격 수')
    ax.grid(axis='y',alpha=.18)
    ax.legend(frameon=False)
    ax=axes[1,1]
    ax.scatter(np.arange(1,n+1),ttft,s=20,color=teal,alpha=.8)
    ax.axhline(d['p95_ttft_ms']/1000,color=orange,linestyle='--',label=f"P95 {d['p95_ttft_ms']/1000:.2f} s")
    ax.set(title='요청별 첫 토큰 대기',xlabel='요청 번호 (저장 순서)',ylabel='TTFT (s)',ylim=(0,max(ttft)*1.12))
    ax.grid(alpha=.18)
    ax.legend(frameon=False)
    localize(fig)
    fig.savefig(out/'baseline-summary.png',dpi=180,facecolor='white')
    plt.close(fig)

    fig,ax=plt.subplots(figsize=(12,12),layout='constrained')
    y=np.arange(1,n+1)
    ax.barh(y,ttft,left=starts,height=.72,color=orange,label='전송 시작 → 첫 토큰 (TTFT)')
    ax.barh(y,latency-ttft,left=starts+ttft,height=.72,color=teal,label='첫 토큰 → 응답 완료')
    ax.invert_yaxis()
    ax.set(xlabel='첫 요청 전송 시작 기준 시간 (s)',ylabel='요청 번호 (저장 순서)',
           title='요청 실행 타임라인 | 클라이언트 전송 전 대기는 표시하지 않음')
    ax.set_yticks([1,16,32,48,64,80,96,100])
    ax.grid(axis='x',alpha=.2)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.055),ncol=2,frameon=False)
    localize(fig)
    fig.savefig(out/'request-timeline.png',dpi=180,facecolor='white')
    plt.close(fig)
    with (out/'requests.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f)
        w.writerow(['request_id','send_start_offset_s','input_tokens','output_tokens','ttft_ms','tpot_ms','e2el_ms','client_queue_s'])
        for i in range(n):
            w.writerow([i+1,starts[i],d['input_lens'][i],d['output_lens'][i],ttft[i]*1000,tpot[i],latency[i]*1000,d.get('queue_times',['']*n)[i]])
    extra = {
        'actual_input_mean':statistics.mean(d['input_lens']),
        'actual_input_min':min(d['input_lens']),
        'actual_input_max':max(d['input_lens']),
        'observed_itl_intervals':len(itl),
        'itl_over_500ms_count':int(np.count_nonzero(itl>500)),
        'itl_over_500ms_percent':float(np.mean(itl>500)*100),
        'kv_metrics_available':False,
        'server_config_source':'User-reported config; startup log not supplied',
        'plot_source':'Official bench per-request JSON; reconstructed report charts, not official plot output',
        'client_queue_note':'Not added to displayed TTFT/E2EL; timeline starts at request send time',
    }
    scalars={k:v for k,v in d.items() if not isinstance(v,(list,dict))}
    (out/'analysis.json').write_text(json.dumps({'benchmark':scalars,'additional_analysis':extra},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(extra,ensure_ascii=False,indent=2))
    print('Saved baseline-summary.png, request-timeline.png, requests.csv, analysis.json')

if __name__=='__main__':
    main()
