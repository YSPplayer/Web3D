#include "bilstm.h"
#include "math.h"
namespace DeepLr::Neural {
	namespace {
		struct LSTMStepCache {
			Tensor3D x;
			Tensor3D z;
			Tensor3D f;
			Tensor3D i;
			Tensor3D g;
			Tensor3D o;
			Tensor3D cPrev;
			Tensor3D c;
			Tensor3D h;
		};

		void ApplySigmoid(Tensor3D& input) {
			for (int32_t i = 0; i < input.Count(); ++i) {
				input.At(i) = DeepLr::Neural::Sigmoid(input.Get(i));
			}
		}

		void ApplyTanh(Tensor3D& input) {
			for (int32_t i = 0; i < input.Count(); ++i) {
				input.At(i) = DeepLr::Neural::Tanh(input.Get(i));
			}
		}

		void AddInPlace(Tensor3D& dst, const Tensor3D& src) {
			for (int32_t i = 0; i < dst.Count(); ++i) {
				dst.At(i) += src.Get(i);
			}
		}

		Tensor3D OuterProduct(const Tensor3D& left, const Tensor3D& right) {
			Tensor3D result(1, right.Height(), left.Height());
			for (int32_t y = 0; y < left.Height(); ++y) {
				for (int32_t x = 0; x < right.Height(); ++x) {
					result.At(0, y, x) = left.Get(0, y, 0) * right.Get(0, x, 0);
				}
			}
			return result;
		}

		Tensor3D MatTransposeVec(const Tensor3D& w, const Tensor3D& grad) {
			Tensor3D result(1, 1, w.Width());
			for (int32_t x = 0; x < w.Width(); ++x) {
				float sum = 0.0f;
				for (int32_t y = 0; y < w.Height(); ++y) {
					sum += w.Get(0, y, x) * grad.Get(0, y, 0);
				}
				result.At(0, x, 0) = sum;
			}
			return result;
		}

		void AccumulateGateGrad(Tensor3D& dw, Tensor3D& db, const Tensor3D& da, const Tensor3D& z) {
			AddInPlace(dw, OuterProduct(da, z));
			AddInPlace(db, da);
		}

		void ResetParGrad(BiLSTMPar& dp, int32_t inputSize, int32_t hiddenSize) {
			auto resetGate = [&](Tensor3D& w, Tensor3D& b) {
				w = Tensor3D(1, inputSize + hiddenSize, hiddenSize);
				b = Tensor3D(1, 1, hiddenSize);
				};
			resetGate(dp.wf, dp.bf);
			resetGate(dp.wi, dp.bi);
			resetGate(dp.wg, dp.bg);
			resetGate(dp.wo, dp.bo);
		}

		void UpdateGate(Tensor3D& w, Tensor3D& b, Tensor3D& dw, Tensor3D& db, float scale) {
			w = w - dw * scale;
			b = b - db * scale;
		}

		void UpdatePar(BiLSTMPar& p, BiLSTMPar& dp, float scale) {
			UpdateGate(p.wf, p.bf, dp.wf, dp.bf, scale);
			UpdateGate(p.wi, p.bi, dp.wi, dp.bi, scale);
			UpdateGate(p.wg, p.bg, dp.wg, dp.bg, scale);
			UpdateGate(p.wo, p.bo, dp.wo, dp.bo, scale);
		}

		std::vector<LSTMStepCache> BuildDirectionCache(
			const Tensor3D& input,
			BiLSTMPar& p,
			int32_t hiddenSize,
			bool reverse) {
			const int32_t T = input.Height();
			std::vector<LSTMStepCache> cache(T);
			Tensor3D h(1, 1, hiddenSize);
			Tensor3D c(1, 1, hiddenSize);
			auto runStep = [&](int32_t t) {
				LSTMStepCache step;
				step.x = Tensor3D::StepInput(input, t);
				step.z = Tensor3D::ConcatHiddenInput(h, step.x);
				step.cPrev = c;
				step.f = p.wf * step.z + p.bf;
				ApplySigmoid(step.f);
				step.i = p.wi * step.z + p.bi;
				ApplySigmoid(step.i);
				step.g = p.wg * step.z + p.bg;
				ApplyTanh(step.g);
				step.o = p.wo * step.z + p.bo;
				ApplySigmoid(step.o);
				step.c = Tensor3D::Hadamard(step.f, step.cPrev) + Tensor3D::Hadamard(step.i, step.g);
				Tensor3D tanhC = step.c;
				ApplyTanh(tanhC);
				step.h = Tensor3D::Hadamard(step.o, tanhC);
				h = step.h;
				c = step.c;
				cache[t] = step;
			};

			if (reverse) {
				for (int32_t t = T - 1; t >= 0; --t) {
					runStep(t);
				}
			}
			else {
				for (int32_t t = 0; t < T; ++t) {
					runStep(t);
				}
			}
			return cache;
		}

		void BackwardDirection(
			const Tensor3D& output,
			const std::vector<LSTMStepCache>& cache,
			const BiLSTMPar& p,
			BiLSTMPar& dp,
			Tensor3D& inputGrad,
			int32_t hiddenSize,
			int32_t inputSize,
			bool reverse) {
			const int32_t T = inputGrad.Height();
			const int32_t outputOffset = reverse ? hiddenSize : 0;
			Tensor3D dhNext(1, 1, hiddenSize);
			Tensor3D dcNext(1, 1, hiddenSize);

			auto runStep = [&](int32_t t) {
				const LSTMStepCache& step = cache[t];
				Tensor3D dh = dhNext;
				for (int32_t i = 0; i < hiddenSize; ++i) {
					dh.At(0, i, 0) += output.Get(0, t, outputOffset + i);
				}

				Tensor3D tanhC = step.c;
				ApplyTanh(tanhC);
				Tensor3D dc = dcNext;
				Tensor3D dao(1, 1, hiddenSize);
				for (int32_t i = 0; i < hiddenSize; ++i) {
					const float dhv = dh.Get(0, i, 0);
					const float ov = step.o.Get(0, i, 0);
					const float tanhCv = tanhC.Get(0, i, 0);
					dao.At(0, i, 0) = dhv * tanhCv * ov * (1.0f - ov);
					dc.At(0, i, 0) += dhv * ov * (1.0f - tanhCv * tanhCv);
				}

				Tensor3D daf(1, 1, hiddenSize);
				Tensor3D dai(1, 1, hiddenSize);
				Tensor3D dag(1, 1, hiddenSize);
				Tensor3D dcPrev(1, 1, hiddenSize);
				for (int32_t i = 0; i < hiddenSize; ++i) {
					const float dcv = dc.Get(0, i, 0);
					const float fv = step.f.Get(0, i, 0);
					const float iv = step.i.Get(0, i, 0);
					const float gv = step.g.Get(0, i, 0);
					const float cPrev = step.cPrev.Get(0, i, 0);
					daf.At(0, i, 0) = dcv * cPrev * fv * (1.0f - fv);
					dai.At(0, i, 0) = dcv * gv * iv * (1.0f - iv);
					dag.At(0, i, 0) = dcv * iv * (1.0f - gv * gv);
					dcPrev.At(0, i, 0) = dcv * fv;
				}

				AccumulateGateGrad(dp.wf, dp.bf, daf, step.z);
				AccumulateGateGrad(dp.wi, dp.bi, dai, step.z);
				AccumulateGateGrad(dp.wg, dp.bg, dag, step.z);
				AccumulateGateGrad(dp.wo, dp.bo, dao, step.z);

				Tensor3D dz(1, 1, hiddenSize + inputSize);
				AddInPlace(dz, MatTransposeVec(p.wf, daf));
				AddInPlace(dz, MatTransposeVec(p.wi, dai));
				AddInPlace(dz, MatTransposeVec(p.wg, dag));
				AddInPlace(dz, MatTransposeVec(p.wo, dao));

				Tensor3D dhPrev(1, 1, hiddenSize);
				for (int32_t i = 0; i < hiddenSize; ++i) {
					dhPrev.At(0, i, 0) = dz.Get(0, i, 0);
				}
				for (int32_t f = 0; f < inputSize; ++f) {
					inputGrad.At(0, t, f) += dz.Get(0, hiddenSize + f, 0);
				}
				dhNext = dhPrev;
				dcNext = dcPrev;
			};

			if (reverse) {
				for (int32_t t = 0; t < T; ++t) {
					runStep(t);
				}
			}
			else {
				for (int32_t t = T - 1; t >= 0; --t) {
					runStep(t);
				}
			}
		}
	}

	BiLSTM::BiLSTM():Layer() {
		ntype = NeuralType::BiLSTM;
		par = std::make_shared<BiLSTMPar>();
		rpar = std::make_shared<BiLSTMPar>();
		dpar = std::make_shared<BiLSTMPar>();
		drpar = std::make_shared<BiLSTMPar>();
		inputSize = 0;
		hiddenSize = 0;
	}
	Tensor3D BiLSTM::Forward(const Tensor3D& input) { // 1,h,w ->1,h,w T,F
		oldx = input;
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
			// 写入内容 c: 生成新的候选信息
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
	Tensor3D BiLSTM::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
		(void)target;
		const int32_t T = oldx.Height();
		const int32_t F = oldx.Width();
		Tensor3D inputGrad(1, F, T);
		const std::vector<LSTMStepCache> forwardCache = BuildDirectionCache(oldx, *par, hiddenSize, false);
		const std::vector<LSTMStepCache> backwardCache = BuildDirectionCache(oldx, *rpar, hiddenSize, true);
		BackwardDirection(output, forwardCache, *par, *dpar, inputGrad, hiddenSize, inputSize, false);
		BackwardDirection(output, backwardCache, *rpar, *drpar, inputGrad, hiddenSize, inputSize, true);
		return inputGrad;
	}
	void BiLSTM::Update(float lr, int32_t batchSize) {
		const float scale = lr / (float)batchSize;
		UpdatePar(*par, *dpar, scale);
		UpdatePar(*rpar, *drpar, scale);
		ResetParGrad(*dpar, inputSize, hiddenSize);
		ResetParGrad(*drpar, inputSize, hiddenSize);
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
		ResetParGrad(*dpar, inputSize, hiddenSize);
		ResetParGrad(*drpar, inputSize, hiddenSize);
	}
	void BiLSTM::Sigmoid(Tensor3D& input) {
		ApplySigmoid(input);
	}
	void BiLSTM::Tanh(Tensor3D& input) {
		ApplyTanh(input);
	}
}
