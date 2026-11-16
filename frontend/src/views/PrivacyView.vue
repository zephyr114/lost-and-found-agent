<script setup lang="ts">
const updated = '2026-11-16'
</script>

<template>
  <div class="legal-page">
    <el-card shadow="never" class="legal-card">
      <h1>隐私政策</h1>
      <p class="legal-meta">生效日期：{{ updated }} · 适用于「杭州电子科技大学失物招领智能平台」</p>

      <p>
        本平台由学生团队自发建设，用于校园失物与招领信息的发布和匹配，<strong>非学校官方平台</strong>。
        我们尽量少收集信息，并只将其用于失物招领本身。
      </p>

      <h2>一、我们收集哪些信息</h2>
      <ul>
        <li><strong>账号信息</strong>：用户名、邮箱；手机号为选填，仅用于登录或联系。</li>
        <li><strong>物品信息</strong>：你发布的标题、描述、类别、颜色、地点、时间与图片。</li>
        <li><strong>认领信息</strong>：认领说明、证明图片、可选联系方式（仅物品发布者与管理员可见）。</li>
        <li><strong>日志信息</strong>：登录时间、IP、Agent 工具调用记录，用于安全审计与故障排查。</li>
      </ul>

      <h2>二、我们如何使用这些信息</h2>
      <ul>
        <li>完成账号注册、登录与身份校验；</li>
        <li>运行智能匹配，把你的失物与招领信息进行比对；</li>
        <li>发送匹配通知、认领结果等站内消息；</li>
        <li>人工审核信息，处理举报与违规内容。</li>
      </ul>

      <h2>三、信息的展示与共享</h2>
      <ul>
        <li>物品信息在审核通过后公开展示，<strong>联系方式默认不公开</strong>。</li>
        <li>认领说明与联系方式仅对物品发布者和管理员可见。</li>
        <li>我们不会向任何第三方出售或出租你的个人信息。</li>
        <li>仅在交接环节，匹配双方可查看完成交接所必需的信息。</li>
      </ul>

      <h2>四、存储与安全</h2>
      <ul>
        <li>数据存储于云数据库（Neon PostgreSQL），网站部署于 Vercel，传输全程 HTTPS。</li>
        <li>密码使用 bcrypt 单向哈希存储，管理员无法看到你的明文密码。</li>
        <li>接口启用限流、权限校验与操作日志。</li>
      </ul>

      <h2>五、你的权利</h2>
      <ul>
        <li>你可以随时查看、修改或删除自己发布的信息与图片。</li>
        <li>如需注销账号或删除全部数据，可联系管理员处理。</li>
        <li>如发现信息有误或泄露，请立即联系我们。</li>
      </ul>

      <h2>六、未成年人</h2>
      <p>未满 18 周岁的用户应在监护人指导下使用本平台，避免填写不必要的个人敏感信息。</p>

      <h2>七、政策更新</h2>
      <p>本政策可能随功能调整而更新，重要变更会在站内公告。继续使用即视为接受更新后的政策。</p>

      <h2>八、联系我们</h2>
      <p>如有疑问、投诉或数据删除请求，请通过站内消息或项目仓库 Issue 联系团队。</p>

      <el-alert type="warning" :closable="false" show-icon class="legal-note">
        提示：请勿在物品描述中填写手机号、学号、宿舍门牌等敏感信息；确需联系时请使用站内消息。
      </el-alert>
    </el-card>
  </div>
</template>

<style scoped>
.legal-page {
  max-width: 820px;
  margin: 0 auto;
}
.legal-card {
  line-height: 1.9;
  color: #cfe3f7;
}
.legal-card h1 {
  margin: 0 0 6px;
  font-size: 26px;
}
.legal-meta {
  margin: 0 0 18px;
  font-size: 12px;
  color: #7f9dbb;
}
.legal-card h2 {
  margin: 22px 0 8px;
  font-size: 16px;
  color: #00e5ff;
}
.legal-card p,
.legal-card li {
  font-size: 14px;
  color: #b9d2e8;
}
.legal-card ul {
  margin: 6px 0;
  padding-left: 20px;
}
.legal-note {
  margin-top: 24px;
}
</style>
