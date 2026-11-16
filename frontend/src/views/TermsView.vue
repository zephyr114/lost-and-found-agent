<script setup lang="ts">
const updated = '2026-11-16'
</script>

<template>
  <div class="legal-page">
    <el-card shadow="never" class="legal-card">
      <h1>用户协议</h1>
      <p class="legal-meta">生效日期：{{ updated }} · 适用于「杭州电子科技大学失物招领智能平台」</p>

      <p>
        欢迎使用本平台。本平台是学生团队自发的公益项目，<strong>非学校官方平台</strong>，
        免费提供失物与招领信息发布、智能匹配、认领与交接辅助。使用前请阅读以下条款。
      </p>

      <h2>一、服务内容</h2>
      <ul>
        <li>发布失物 / 招领信息，浏览与检索公开信息；</li>
        <li>基于规则的智能匹配、匹配解释与交接码；</li>
        <li>认领申请、站内消息、举报与人工审核。</li>
      </ul>
      <p>服务按「现状」提供，我们尽力维护，但不承诺永不中断或一定能找回物品。</p>

      <h2>二、账号规则</h2>
      <ul>
        <li>请使用真实、可联系的信息注册，不得冒用他人身份；</li>
        <li>账号仅限本人使用，不得出租、出售或共享；</li>
        <li>发现账号异常请及时修改密码并联系管理员。</li>
      </ul>

      <h2>三、发布规范</h2>
      <ul>
        <li>禁止发布违法、虚假、欺诈、广告、色情或侵犯他人隐私的内容；</li>
        <li>请勿在公开描述中填写手机号、学号、身份证号、宿舍门牌等敏感信息；</li>
        <li>图片应为你本人拍摄或有权使用的图片；</li>
        <li>所有信息需经人工审核后公开展示，我们有权删除违规内容并封禁账号。</li>
      </ul>

      <h2>四、认领与交接</h2>
      <ul>
        <li>认领人应如实描述物品特征，<strong>冒领他人财物须自行承担相应责任</strong>；</li>
        <li>交接码 / 二维码仅用于核对身份，请勿转发给无关人员；</li>
        <li>建议在公共场所当面交接，平台不参与线下交接，不对交接纠纷承担责任；</li>
        <li>拾获者应妥善保管物品，及时归还或交由学校相关部门。</li>
      </ul>

      <h2>五、知识产权</h2>
      <p>你发布的内容归你所有；你授权平台在提供服务所必需的范围内展示、存储与处理这些内容。</p>

      <h2>六、免责声明</h2>
      <ul>
        <li>平台不保证一定能匹配到失物或完成找回；</li>
        <li>因网络、设备、不可抗力导致的服务中断或数据延迟，平台不承担责任；</li>
        <li>用户之间因线下交接产生的纠纷，由双方自行协商解决。</li>
      </ul>

      <h2>七、协议变更</h2>
      <p>我们可能根据功能与法规变化更新本协议，重要变更会在站内公告。继续使用即视为接受更新后的协议。</p>

      <h2>八、联系我们</h2>
      <p>如对协议有疑问，请通过站内消息或项目仓库 Issue 联系团队。</p>
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
</style>
