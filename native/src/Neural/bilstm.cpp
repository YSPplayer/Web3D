#include "bilstm.h"
#include "math.h"
namespace DeepLr::Neural {
	BiLSTM::BiLSTM():Layer() {
		ntype = NeuralType::BiLSTM;
		par = std::make_shared<BiLSTMPar>();
		rpar = std::make_shared<BiLSTMPar>();
		inputSize = 0;
		hiddenSize = 0;
	}
	Tensor3D BiLSTM::Forward(const Tensor3D& input) { // 1,h,w ->1,h,w T,F
		const int32_t T = input.Height();
		const int32_t F = input.Width();
		std::vector<Tensor3D> forward(T);
		std::vector<Tensor3D> backward(T);
		Tensor3D hf(1, 1, hiddenSize); //短期信息输出(隐藏状态)
		Tensor3D cf(1, 1, hiddenSize); //长期信息累加(细胞状态)
		for (int32_t t = 0; t < T; ++t) {
			// 1. 获取当前时间步的输入
			const Tensor3D& x = Tensor3D::StepInput(input,t); //获取到当前的这一个时间序列块的对象  (1, 1, F)
			// 2. 合并上一个隐藏状态和当前输入 
			const Tensor3D& z = Tensor3D::ConcatHiddenInput(hf,x);//合并上一次结果形成新的数据  z = [h_{t-1}; x_t]，形状: (1, 1, hiddenSize + F)
			// 3. LSTM门控计算
			// 擦除比例， 遗忘门: 决定丢弃多少旧信息
			Tensor3D ft = par->wf * z + par->bf; // 权重矩阵 × 拼接向量 + 偏置
			Sigmoid(ft);// 输出范围 [0,1]
			// 写入比例 输入门: 决定写入多少新信息
			Tensor3D it = par->wi * z + par->bi;
			Sigmoid(it);
			// 写入内容 候选记忆: 生成新的候选信息
			Tensor3D gt = par->wg * z + par->bg;
			Tanh(gt); // 输出范围 [-1,1]
			// 输出过滤旋钮 输出门: 决定输出多少记忆
			Tensor3D ot = par->wo * z + par->bo;
			Sigmoid(ot);
			// 4. 更新细胞状态
			// c_t = f_t ⊙ c_{t-1} + i_t ⊙ g_t 按比例保持旧仓库 + 添加新的学习内容
			cf = Tensor3D::Hadamard(ft, cf) + Tensor3D::Hadamard(it, gt);
			// 5. 计算隐藏状态
			// h_t = o_t ⊙ tanh(c_t)
			Tensor3D tanhC = cf; 
			Tanh(tanhC); //标准化仓库内存，把所有值压缩在-1~1之间，归一化
			// 6. 保存当前时刻的前向隐藏状态
			hf = Tensor3D::Hadamard(ot, tanhC); //按比例输出
			forward[t] = hf;
		}

		Tensor3D hb(1, 1, hiddenSize);
		Tensor3D cb(1, 1, hiddenSize);
		for (int32_t t = T - 1; t >= 0; --t) {
			const Tensor3D& x = Tensor3D::StepInput(input, t);
			const Tensor3D& z = Tensor3D::ConcatHiddenInput(hb, x);
			Tensor3D ft = rpar->wf * z + rpar->bf;
			Sigmoid(ft);
			Tensor3D it = rpar->wi * z + rpar->bi;
			Sigmoid(it);
			Tensor3D gt = rpar->wg * z + rpar->bg;
			Tanh(gt);
			Tensor3D ot = rpar->wo * z + rpar->bo;
			Sigmoid(ot);
			cb = Tensor3D::Hadamard(ft, cb) + Tensor3D::Hadamard(it, gt);
			Tensor3D tanhC = cb;
			Tanh(tanhC);
			hb = Tensor3D::Hadamard(ot, tanhC);
			backward[t] = hb;
		}
		Tensor3D output(1, hiddenSize * 2, T);  // 形状: (1, 2×hiddenSize, T)
		for (int32_t t = 0; t < T; ++t) {
			for (int32_t i = 0; i < hiddenSize; ++i) {
				// 拼接前向和后向的隐藏状态
				output.At(0, t, i) = forward[t].Get(0, i, 0); // 前向
				output.At(0, t, hiddenSize + i) = backward[t].Get(0, i, 0); // 后向
			}
		}
		return output;
	}
	void BiLSTM::SetShape(const TensorShape& lastshape, const TensorShape& shape) {
		Layer::SetShape(lastshape, shape);
		inputSize = lastshape.w;
		hiddenSize = shape.w / 2;
		auto initGate = [&](Tensor3D& w, Tensor3D& b) {
			w = Tensor3D(1, inputSize + hiddenSize, hiddenSize);
			w.HeUniform(inputSize + hiddenSize);
			b = Tensor3D(1, 1, hiddenSize);
			};
		initGate(par->wf, par->bf);
		initGate(par->wi, par->bi);
		initGate(par->wg, par->bg);
		initGate(par->wo, par->bo);

		initGate(rpar->wf, rpar->bf);
		initGate(rpar->wi, rpar->bi);
		initGate(rpar->wg, rpar->bg);
		initGate(rpar->wo, rpar->bo);
	}
	void BiLSTM::Sigmoid(Tensor3D& input) {
		const auto& fv = input.Data();
		std::transform(fv.begin(), fv.end(), fv.begin(), [](float x) {
			return DeepLr::Neural::Sigmoid(x);
		});
	}
	void BiLSTM::Tanh(Tensor3D& input) {
		const auto& fv = input.Data();
		std::transform(fv.begin(), fv.end(), fv.begin(), [](float x) {
			return DeepLr::Neural::Tanh(x);
			});
	}
}
