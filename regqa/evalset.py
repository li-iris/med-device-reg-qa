"""评测题。每题标注：类型、标准答案所在条款（gold，可多个都算对）、该题的「陷阱条款」（答成它就是错版本）。

类型
- current   现行规定（其中 trap 题：2017→2021 内容变了，答成旧版就是质量事故）
- history   明确问旧版 / 修订前
- exact     按条号查
- ae        不良事件监测办法
- none      资料库里没有答案（应拒答）

DEV 用于调参；HOLDOUT 在调参结束后才写，只跑一次，单独报告。
"""
DEV = [
    # 现行规定：版本陷阱
    dict(q="第三类医疗器械经营许可，药监部门要在多少个工作日内作出决定？", type="current", gold=["reg2021-042"], trap=["reg2017-031"]),
    dict(q="申请二类、三类医疗器械生产许可，审查时限是多少个工作日？", type="current", gold=["reg2021-032"], trap=["reg2017-022"]),
    dict(q="未取得医疗器械注册证生产第二类医疗器械，货值1万元以上罚款多少倍？", type="current", gold=["reg2021-081"], trap=["reg2017-063"]),
    dict(q="哪些情况可以免于进行临床评价？", type="current", gold=["reg2021-024"], trap=["reg2017-017"]),
    dict(q="委托生产医疗器械，由谁对产品质量负责？", type="current", gold=["reg2021-034"], trap=["reg2017-028"]),
    dict(q="发现产品存在缺陷，召回由谁负责实施？", type="current", gold=["reg2021-067"], trap=["reg2017-052"]),
    dict(q="医疗器械注册人、备案人应当履行哪些义务？", type="current", gold=["reg2021-020"], trap=[]),
    dict(q="医疗器械唯一标识制度是怎么规定的？", type="current", gold=["reg2021-038"], trap=[]),
    dict(q="医疗器械临床试验的伦理审查和知情同意有什么要求？", type="current", gold=["reg2021-028"], trap=[]),
    dict(q="罕见病急需的医疗器械能不能附条件批准？", type="current", gold=["reg2021-019"], trap=[]),
    dict(q="医疗器械注册证有效期几年，什么时候申请延续？", type="current", gold=["reg2021-022"], trap=["reg2017-015"]),
    dict(q="医疗器械网络销售有什么要求？", type="current", gold=["reg2021-046"], trap=[]),
    # 历史版本
    dict(q="2017年版条例里，第三类经营许可的审查时限是多少？", type="history", gold=["reg2017-031"], trap=["reg2021-042"]),
    dict(q="修订前的条例对无证生产的罚款是货值金额多少倍？", type="history", gold=["reg2017-063"], trap=["reg2021-081"]),
    dict(q="旧版条例规定哪些情形可以免于临床试验？", type="history", gold=["reg2017-017"], trap=["reg2021-024"]),
    # 条号
    dict(q="条例第三十八条规定了什么？", type="exact", gold=["reg2021-038"], trap=[]),
    dict(q="不良事件办法第二十五条", type="exact", gold=["ae2018-025"], trap=[]),
    # 不良事件办法
    dict(q="可疑不良事件导致死亡的，持有人应当在多少日内报告？", type="ae", gold=["ae2018-025"], trap=[]),
    dict(q="发生群体医疗器械不良事件，多长时间内要电话报告？", type="ae", gold=["ae2018-031", "ae2018-033"], trap=[]),
    dict(q="定期风险评价报告什么时候完成？", type="ae", gold=["ae2018-039"], trap=[]),
    dict(q="什么是严重伤害？", type="ae", gold=["ae2018-004"], trap=[]),
    # 无答案
    dict(q="洁净室的悬浮粒子标准是多少？", type="none", gold=[], trap=[]),
    dict(q="医疗器械经营企业的增值税税率是多少？", type="none", gold=[], trap=[]),
    dict(q="条例第一百二十条是什么内容？", type="none", gold=[], trap=[]),
]

HOLDOUT = [
    dict(q="现在申请第三类医疗器械经营许可，审批要多久？", type="current", gold=["reg2021-042"], trap=["reg2017-031"]),
    dict(q="没拿到许可证就生产医疗器械，会被怎么处罚？", type="current", gold=["reg2021-081"], trap=["reg2017-063"]),
    dict(q="注册人可以把生产外包给别的工厂吗？", type="current", gold=["reg2021-034"], trap=["reg2017-028"]),
    dict(q="产品追溯用的 UDI 有法规依据吗？", type="current", gold=["reg2021-038"], trap=[]),
    dict(q="进口医疗器械的说明书必须是中文吗？", type="current", gold=["reg2021-057"], trap=[]),
    dict(q="以前的条例要求生产许可多少个工作日审完？", type="history", gold=["reg2017-022"], trap=["reg2021-032"]),
    dict(q="办法第三十九条讲什么？", type="exact", gold=["ae2018-039"], trap=[]),
    dict(q="境外发生严重不良事件，国产器械的持有人多少天内要报告？", type="ae", gold=["ae2018-027"], trap=[]),
    dict(q="发生群体不良事件后，持有人要不要停产？", type="ae", gold=["ae2018-032"], trap=[]),
    dict(q="持有人主动再评价后，多久内提交再评价报告？", type="ae", gold=["ae2018-058"], trap=[]),
    dict(q="2025年新版生产质量管理规范新增了哪些章节？", type="none", gold=[], trap=[]),
    dict(q="医疗器械能进医保目录吗？", type="none", gold=[], trap=[]),
]

# 第二轮留出集：看到 HOLDOUT 的失败（口语说法对不上法规用语）、加了同义词改写之后才写的新题，
# 用来检验改写是否真的泛化，而不是只修好了那几道题。
HOLDOUT2 = [
    dict(q="现在开一家卖三类器械的店，许可证审批多长时间？", type="current", gold=["reg2021-042"], trap=["reg2017-031"]),
    dict(q="找代工厂生产，出了质量问题谁担责？", type="current", gold=["reg2021-034"], trap=["reg2017-028"]),
    dict(q="没有注册证就卖二类器械，罚款怎么算？", type="current", gold=["reg2021-081"], trap=["reg2017-063"]),
    dict(q="器械标签上必须写哪些内容？", type="current", gold=["reg2021-039"], trap=["reg2017-027"]),
    dict(q="医院发现可疑不良事件要告诉谁？", type="ae", gold=["ae2018-025"], trap=[]),
    dict(q="群体不良事件要多少小时内报告？", type="ae", gold=["ae2018-031", "ae2018-033"], trap=[]),
    dict(q="什么是群体医疗器械不良事件？", type="ae", gold=["ae2018-004"], trap=[]),
    dict(q="原条例里委托生产的规定是什么？", type="history", gold=["reg2017-028"], trap=["reg2021-034"]),
    dict(q="条例第二十条", type="exact", gold=["reg2021-020"], trap=[]),
    dict(q="医疗器械出口美国要做 FDA 510(k) 吗？", type="none", gold=[], trap=[]),
    dict(q="医用口罩的过滤效率标准是多少？", type="none", gold=[], trap=[]),
]
