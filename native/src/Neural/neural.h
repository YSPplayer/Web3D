#pragma once
#include "../data.h"
#include <vector>
#include <memory>
#include <random>
#include "layer.h"
#include "sample.h"
#include "loss.h"
#include <any>
namespace DeepLr::Neural {
	class Neural {
	public:
		Neural(TensorShape tensorShape,const std::vector<NeuralBuild>& builds);
		Neural();
		static std::shared_ptr<Neural> BuildDefaultNeural();
		void Train(std::vector<std::string>& files, int32_t maxEpoch = 5, int32_t batch = 32,float lr = 0.01f);
		void Validate(std::vector<std::string>& files);
		void GetNeural(std::vector<NeuralBuild>& builds, std::vector<std::any> &cores);
		bool SaveModel(const std::string& filename);
		bool Predict(const Tensor3D& input, std::array<int32_t, 4>& array, Tensor3D& output);
		bool InitFromModel(const std::string& filename);
	private:
		std::array<int32_t, 4> TensorToLabel(const Tensor3D& input);
		std::vector<Layer*> neural;
		Loss loss;
		Tensor3D Predict(const Tensor3D& input);
		float TrainBatch(const std::vector<std::shared_ptr<Sample>>& samples,float lr);
		float TrainBatchParallel(const std::vector<std::shared_ptr<Sample>>& samples, float lr, int32_t threadCount = 8);
		float TrainBatchNoUpdate(const std::vector<std::shared_ptr<Sample>>& samples, bool debugBatch);
		void Crear();
		void SetBuilds(const std::vector<NeuralBuild>& builds);
		void SetCores(const std::vector<std::any>& cores);
		void ClearGrad();
		void AccumulateGradFrom(const Neural& other);
		void WriteTensor3D(const Tensor3D& tensor, std::vector<char>& buffer);
		Tensor3D ReadTensor3D(const std::vector<char>& buffer, int32_t& offset);
		bool WriteToBinaryFile(const std::string& filename, const std::vector<char>& buffer);
		bool ReadFromBinaryFile(const std::string& filename, std::vector<char>& buffer);
		static std::shared_ptr<std::mt19937> g;
		TensorShape inputShape;
	};
}