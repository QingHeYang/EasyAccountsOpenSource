# AI+ 功能描述  
## 界面描述
AI+是一个对话流界面  
有两方，一方是用户，一方是AI，用户可以输入问题，AI可以回答问题  
所以要求界面，下方有一个输入框，限制100字，还有发送按钮，发送按钮点击后，清空输入框，并且loading，不可以点击发送，直到收到结束信号。  
ai的对话框颜色是浅灰色底深灰色字，用户是蓝底白字，均为圆角，圆角大小为10px。  
界面要求是实时刷新的，websocket传入的是一个文本chunk+一个文本chunk，轮番传入，所以要求实时刷新  
ai对话框要求可以解析markdown，使用markdown-it库解析，要求有思维链，可以解析思维链并折叠  
ai对话框分为  
* segment：segment是一堆分片的合集，当收到一个segment时，删掉上一个segment之后的所有chunk，并显示当前的segment（因为chunk拼接起来就是后面的segment，并且这个segment被我处理过了）  
* tool: tool是websocket发送的一种数据类型，分为 1. tool_call，2. tool_response，这两个一般是tool_call先传进来，tool_response后传进来，中间绝对不会进入任何信息，他们俩要求组成一个tool对话框，当tool_call收到后，对话框要求loading，当tool_response收到后，对话框要求loading结束，并且显示成功与否，tool_对话框要求可以点击，点击弹出来一个弹窗，显示tool详情  

ai对话框进入的顺序一般不固定，tool_call和tool_response成对出现，前面后面可能是segment等等  

用户对话框就正常显示即可  

对话列表可以向上滚动，每个对话框下方需要标识出来发送时间  

整个界面需要有链接状态，顶部的title栏目，一开始命名是“AI+”，后面接到websocket的时候，他会给出具体的title名称，直接赋值即可，另外获取历史的时候，也会把title给携带过来

## 逻辑描述  
数据： 分为两种，一种是websocket传入的，一种是http传入的  
http传入的一般是历史，进入界面后会获取历史，如果缓存中没有conversation_id，则无需调用
有的话要调用历史接口，获取数据后，要解析成为对话框显示。  
webkcoket传入的是实时传入的，用户对话的时候，一条一条的显示即可  

如果缓存中没有conversation_id，开始对话时，conversation_id直接传空就行，但是后续的websocket返回值中会有conversation_id，需要缓存下来  

## 接口描述  

./message.curl 获取历史
./message.json 历史返回值
./websocket.request 发送websocket请求
./websocket.response 发送websocket返回值